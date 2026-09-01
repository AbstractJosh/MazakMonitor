/* main.c — UDP listener wiring: transport -> reassembly -> decode -> print,
 * with config wiring, state save/load, and optional xlsx logging.
 * Cross-platform sockets (Windows Winsock / POSIX).
 *
 *   promos3_reader [--raw|--decode] [--port N]
 *                  [--config FILE.pmd] [--config-unit N=FILE.pmd]
 *                  [--state FILE] [--xlsx FILE.xlsx] [--dump]
 */
#include "promos3.h"
#include "promos3_state.h"
#include "xlsx.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <signal.h>

#ifdef _WIN32
  #include <winsock2.h>
  #include <ws2tcpip.h>
  #define CLOSESOCK closesocket
  typedef int sock_t;
#else
  #include <unistd.h>
  #include <arpa/inet.h>
  #include <sys/socket.h>
  #define CLOSESOCK close
  typedef int sock_t;
#endif

static volatile sig_atomic_t g_stop = 0;
static void on_sigint(int s) { (void)s; g_stop = 1; }

static void iso_now(char *out, size_t n) {
    time_t t = time(NULL);
    struct tm *tm = localtime(&t);            /* single-threaded: fine        */
    if (tm) strftime(out, n, "%Y-%m-%d %H:%M:%S", tm);
    else    snprintf(out, n, "?");
}

static void log_row(xlsx_t *x, const promos3_msg_t *m, const reader_state_t *st) {
    if (!x) return;
    char ts[32]; iso_now(ts, sizeof ts);
    xlsx_row_begin(x);
    xlsx_cell_str(x, ts);
    xlsx_cell_num(x, m->unit);
    if (!m->parsed) {
        xlsx_cell_str(x, "[UNPARSED]");
        xlsx_cell_str(x, ""); xlsx_cell_str(x, "");
        xlsx_cell_num(x, (double)m->raw_len);
        xlsx_row_end(x);
        return;
    }
    xlsx_cell_str(x, cmd_name(m->group, m->command));
    if (cmd_confidence(m->group, m->command) == CONF_CONFIRMED
        && m->group == GROUP_MC && m->command == 0x1B) {
        signalverlauf_t sv;
        if (decode_signalverlauf(m, &sv)) {
            xlsx_cell_str(x, reader_feature_name(st, m->unit, sv.channel_key));
            xlsx_cell_num(x, sv.vmin);
            xlsx_cell_num(x, sv.vmax);
        } else { xlsx_cell_str(x, ""); xlsx_cell_str(x, ""); xlsx_cell_str(x, ""); }
    } else {
        xlsx_cell_str(x, "");
        xlsx_cell_str(x, "");
        xlsx_cell_num(x, (double)m->body_len);
    }
    xlsx_row_end(x);
}

int main(int argc, char **argv) {
    int   decode = 0, dump = 0;
    int   port   = PROMOS3_UDP_PORT;
    const char *config_path = NULL, *state_path = NULL, *xlsx_path = NULL;
    setvbuf(stdout, NULL, _IOLBF, 0);

    for (int i = 1; i < argc; i++) {
        if      (!strcmp(argv[i], "--decode")) decode = 1;
        else if (!strcmp(argv[i], "--raw"))    decode = 0;
        else if (!strcmp(argv[i], "--dump"))   dump   = 1;
        else if (!strcmp(argv[i], "--port")   && i+1 < argc) port        = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--config") && i+1 < argc) config_path = argv[++i];
        else if (!strcmp(argv[i], "--state")  && i+1 < argc) state_path  = argv[++i];
        else if (!strcmp(argv[i], "--xlsx")   && i+1 < argc) xlsx_path   = argv[++i];
        else if (!strcmp(argv[i], "--config-unit") && i+1 < argc) i++;   /* handled below */
        else { fprintf(stderr, "unknown arg: %s\n", argv[i]); return 2; }
    }

    reader_state_t st;
    reader_state_init(&st);
    if (state_path && reader_state_load(state_path, &st))
        fprintf(stderr, "state: loaded %s\n", state_path);

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--config-unit") || i + 1 >= argc) continue;
        char spec[512]; snprintf(spec, sizeof spec, "%s", argv[++i]);
        char *eq = strchr(spec, '=');
        if (!eq) { fprintf(stderr, "config-unit: expected N=FILE, got %s\n", spec); continue; }
        *eq = 0; int u = atoi(spec);
        if (reader_apply_pmd(&st, u, eq + 1)) fprintf(stderr, "config: unit %d <- %s\n", u, eq + 1);
        else                                  fprintf(stderr, "config: FAILED unit %d <- %s\n", u, eq + 1);
    }

    if (dump) {
        if (config_path) reader_apply_pmd(&st, -1, config_path);
        reader_state_dump(&st);
        return 0;
    }
    if (config_path) {
        if (reader_apply_pmd(&st, -1, config_path))
            fprintf(stderr, "config: loaded %s (all units)\n", config_path);
        else
            fprintf(stderr, "config: FAILED to load %s\n", config_path);
    }

    xlsx_t *xl = NULL;
    if (xlsx_path) {
        xl = xlsx_open(xlsx_path, "PROVIS3");
        if (xl) {
            xlsx_row_begin(xl);
            const char *hdr[] = {"time","unit","command","feature","min","max/len"};
            for (int i = 0; i < 6; i++) xlsx_cell_str(xl, hdr[i]);
            xlsx_row_end(xl);
        } else fprintf(stderr, "xlsx: cannot open %s\n", xlsx_path);
    }

#ifdef _WIN32
    WSADATA wsa;
    if (WSAStartup(MAKEWORD(2,2), &wsa) != 0) { fprintf(stderr, "WSAStartup failed\n"); return 1; }
#endif

    sock_t fd = socket(AF_INET, SOCK_DGRAM, 0);
    if (fd < 0) { perror("socket"); return 1; }
    int one = 1; setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, (const char *)&one, sizeof one);
    struct sockaddr_in addr; memset(&addr, 0, sizeof addr);
    addr.sin_family = AF_INET; addr.sin_addr.s_addr = htonl(INADDR_ANY);
    addr.sin_port = htons((unsigned short)port);
    if (bind(fd, (struct sockaddr *)&addr, sizeof addr) < 0) { perror("bind"); return 1; }

    signal(SIGINT, on_sigint);

    fprintf(stderr, "listening UDP :%d  mode=%s%s%s\n", port, decode ? "DECODE" : "RAW",
            config_path ? "  +config" : "", xlsx_path ? "  +xlsx" : "");

    reasm_ctx_t reasm; reasm_init(&reasm);
    static uint8_t dg[65536];

    while (!g_stop) {
        struct sockaddr_in from; socklen_t fl = sizeof from;
        int n = (int)recvfrom(fd, (char *)dg, (int)sizeof dg, 0, (struct sockaddr *)&from, &fl);
        if (n <= 0) continue;

        size_t len = (size_t)n;
        for (size_t off = len % GW_RECORD_SIZE; off + GW_RECORD_SIZE <= len; off += GW_RECORD_SIZE) {
            can_frame_t f;
            gw_parse_record(dg + off, &f);
            if (!decode) { print_can_frame(&f); continue; }

            promos3_msg_t m;
            if (reasm_feed(&reasm, &f, &m)) {
                reader_state_update(&st, &m);
                print_message(&m, &st);
                log_row(xl, &m, &st);
            }
        }
    }

    fprintf(stderr, "\nshutting down...\n");
    if (xl && xlsx_close(xl)) fprintf(stderr, "xlsx: wrote %s\n", xlsx_path);
    if (state_path && reader_state_save(state_path, &st))
        fprintf(stderr, "state: saved %s\n", state_path);
    CLOSESOCK(fd);
#ifdef _WIN32
    WSACleanup();
#endif
    return 0;
}
