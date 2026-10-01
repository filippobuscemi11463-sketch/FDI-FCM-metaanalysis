#!/usr/bin/env Rscript
# Meta-analisi RCT testa a testa FDI vs FCM — protocollo 99-Meta/protocollo-metanalisi.md §11.
#
#   Rscript 50-Metanalisi/analisi.R            (dalla radice del vault)
#
# Legge SOLO 30-Dati/ma-bracci.csv (righe usa_in_analisi = si), ma-trial.csv e
# ma-rob2.csv; scrive in 50-Metanalisi/output/. Nessun numero aggregato si
# scrive a mano: tutto ciò che sta in output/ lo produce questo script.
#
# Direzione: RR, OR e RD sono FDI rispetto a FCM (RR < 1: meno eventi con FDI).
# MD = FDI − FCM, in mmol/L.

suppressPackageStartupMessages({
  library(metafor)
  library(digest)
})

RADICE <- normalizePath(".")
stopifnot(file.exists(file.path(RADICE, "CLAUDE.md")))
OUT <- file.path(RADICE, "50-Metanalisi", "output")
dir.create(file.path(OUT, "forest"), recursive = TRUE, showWarnings = FALSE)

F_BRACCI <- file.path(RADICE, "30-Dati", "ma-bracci.csv")
F_TRIAL  <- file.path(RADICE, "30-Dati", "ma-trial.csv")
F_ROB    <- file.path(RADICE, "30-Dati", "ma-rob2.csv")

leggi <- function(f) read.csv(f, colClasses = "character", na.strings = "",
                              encoding = "UTF-8", check.names = FALSE)
bracci <- leggi(F_BRACCI)
trial  <- leggi(F_TRIAL)
rob    <- leggi(F_ROB)
sottogruppi <- leggi(file.path(RADICE, "50-Metanalisi", "sottogruppi.csv"))  # classificazione esplorativa (§11)

# ---- costanti del protocollo ------------------------------------------------
DICOTOMICI <- c("P1", "S1", "S2", "S3", "S5", "S6", "S7", "S8a", "S8b")
RARI       <- c("S5", "S6", "S7", "S8a", "S8b")          # §11, eventi rari
SOGLIA     <- c(P1 = 0.65, S1 = 0.32, S2 = 0.80, S3 = 0.65)  # §6.1-6.2, mmol/L
MGDL_MMOL  <- 0.3229                                      # fosfato: mg/dL → mmol/L
K_MIN      <- 2                                           # aggregazione minima (§11)
ESITI_63   <- c("S5", "S6")                               # §6.3: anche K_MIN trial con eventi
FONTI_DEBOLI <- c("registro", "abstract")                 # sensibilità 5

num <- function(x) suppressWarnings(as.numeric(x))

# ---- tracciabilità (§13) ----------------------------------------------------
checksum <- digest(file = F_BRACCI, algo = "sha256")
commit <- tryCatch(system("git rev-parse --short HEAD", intern = TRUE),
                   error = function(e) "sconosciuto")
sporco <- length(tryCatch(system("git status --porcelain -- 50-Metanalisi/analisi.R 30-Dati",
                                 intern = TRUE), error = function(e) character())) > 0

# ---- preparazione: una riga per trial × esito × finestra × braccio ----------
usati <- bracci[bracci$usa_in_analisi == "si", ]
esclusi <- data.frame(trial_id = character(), esito = character(), finestra = character(),
                      motivo = character())
escludi <- function(t, e, f, m) {
  esclusi[nrow(esclusi) + 1, ] <<- list(t, e, f, m)
}

chiave <- paste(usati$trial_id, usati$esito, usati$finestra, sep = "\r")
dati <- list()
for (k in unique(chiave)) {
  g <- usati[chiave == k, ]
  t <- g$trial_id[1]; e <- g$esito[1]; f <- g$finestra[1]
  riga <- list(trial_id = t, esito = e, finestra = f)
  ok <- TRUE
  for (farm in c("FDI", "FCM")) {
    b <- g[g$farmaco == farm, ]
    if (nrow(b) == 0) { escludi(t, e, f, paste("nessuna riga usata per", farm)); ok <- FALSE; break }
    n <- unique(num(b$n_analizzati))
    if (length(n) != 1 || is.na(n)) {
      escludi(t, e, f, paste("n_analizzati mancante o non univoco per", farm)); ok <- FALSE; break
    }
    if (e %in% DICOTOMICI) {
      ev <- num(b$n_eventi)
      if (anyNA(ev)) { escludi(t, e, f, paste("n_eventi mancante per", farm)); ok <- FALSE; break }
      # S8b: una riga per SOC; la somma è un conteggio di pazienti esatto solo
      # se al più una SOC ha eventi nel braccio (codebook §6 regola 4).
      if (nrow(b) > 1) {
        if (e != "S8b" || sum(ev > 0) > 1) {
          escludi(t, e, f, paste("più righe usate non sommabili per", farm)); ok <- FALSE; break
        }
      }
      riga[[paste0("ev_", farm)]] <- sum(ev)
    } else {
      if (nrow(b) != 1) { escludi(t, e, f, paste("più righe continue per", farm)); ok <- FALSE; break }
      m <- num(b$media); s <- num(b$ds)
      if (is.na(m) || is.na(s) || b$tipo_dispersione != "ds") {
        escludi(t, e, f, paste("media o DS mancante per", farm)); ok <- FALSE; break
      }
      conv <- switch(b$unita, "mg/dL" = MGDL_MMOL, "mmol/L" = 1, NA)
      if (is.na(conv)) { escludi(t, e, f, paste("unità non gestita:", b$unita)); ok <- FALSE; break }
      riga[[paste0("m_", farm)]] <- m * conv
      riga[[paste0("sd_", farm)]] <- s * conv
      riga$misura_continua <- b$misura_continua
    }
    riga[[paste0("n_", farm)]] <- n
    riga[[paste0("sede_", farm)]] <- paste(unique(paste(b$pmid, b$pagina_o_tabella, sep = ": ")), collapse = " | ")
    riga$soglia <- num(b$soglia_mmol_l[1])
    riga$fonte_dato <- paste(sort(unique(c(riga$fonte_dato, b$fonte_dato))), collapse = "+")
  }
  if (ok) dati[[length(dati) + 1]] <- riga
}
tutti_campi <- unique(unlist(lapply(dati, names)))
dati <- do.call(rbind, lapply(dati, function(r) {
  r[setdiff(tutti_campi, names(r))] <- NA
  as.data.frame(r[tutti_campi], stringsAsFactors = FALSE)
}))

# caratteristiche per le sensibilità
dati$acronimo <- trial$acronimo[match(dati$trial_id, trial$trial_id)]
dati$etichetta <- ifelse(is.na(dati$acronimo) | dati$acronimo == "", dati$trial_id, dati$acronimo)
dati$produttore <- trial$produttore_coinvolto[match(dati$trial_id, trial$trial_id)]
dati$rob <- rob$complessivo[match(paste(dati$trial_id, dati$esito), paste(rob$trial_id, rob$esito))]

write.csv(dati, file.path(OUT, "input-analisi.csv"), row.names = FALSE, na = "")

# ---- modelli ----------------------------------------------------------------
risultati <- list()
aggiungi <- function(d, e, f, analisi, modello, misura, fit = NULL, nota = "") {
  r <- list(esito = e, finestra = f, analisi = analisi, modello = modello, misura = misura,
            k = nrow(d), trial = paste(d$etichetta, collapse = "; "),
            stima = NA, ic_inf = NA, ic_sup = NA, p = NA, tau2 = NA, i2 = NA, q = NA, q_p = NA,
            pi_inf = NA, pi_sup = NA, nota = nota)
  if (!is.null(fit)) {
    tr <- if (misura %in% c("RR", "OR")) exp else identity
    r$k <- fit$k
    r$stima <- tr(as.numeric(fit$b)); r$ic_inf <- tr(fit$ci.lb); r$ic_sup <- tr(fit$ci.ub)
    r$p <- fit$pval
    if (!is.finite(as.numeric(fit$b)))
      r$nota <- "stima non definita: nessun evento in uno dei due bracci aggregati (log 0)"
    if (!is.null(fit$tau2)) r$tau2 <- fit$tau2
    if (!is.null(fit$I2)) r$i2 <- fit$I2
    if (!is.null(fit$QE)) { r$q <- fit$QE; r$q_p <- fit$QEp }
    if (inherits(fit, "rma.uni") && fit$method != "FE" && fit$k >= 3) {
      pr <- predict(fit)
      r$pi_inf <- tr(pr$pi.lb); r$pi_sup <- tr(pr$pi.ub)
    }
  }
  if (e %in% DICOTOMICI && nrow(d) > 0) {
    r$eventi_fdi <- sprintf("%d/%d", sum(d$ev_FDI), sum(d$n_FDI))
    r$eventi_fcm <- sprintf("%d/%d", sum(d$ev_FCM), sum(d$n_FCM))
  }
  risultati[[length(risultati) + 1]] <<- r
}
prova <- function(expr) tryCatch(expr, error = function(err) structure(conditionMessage(err), class = "errore"))
fallito <- function(x) inherits(x, "errore")

# modello REML + HKSJ su log RR, senza correzione di continuità (solo trial senza celle zero)
reml_rr <- function(d, add = 0) {
  if (add == 0) d <- d[d$ev_FDI > 0 & d$ev_FCM > 0 & d$ev_FDI < d$n_FDI & d$ev_FCM < d$n_FCM, ]
  if (nrow(d) < K_MIN) return(NULL)
  rma(measure = "RR", ai = ev_FDI, n1i = n_FDI, ci = ev_FCM, n2i = n_FCM, data = d,
      method = "REML", test = "knha", add = add, to = "only0", drop00 = TRUE)
}
mh <- function(d, misura = "RR") {
  if (misura != "RD") d <- d[!(d$ev_FDI == 0 & d$ev_FCM == 0), ]
  if (nrow(d) < K_MIN) return(NULL)
  rma.mh(measure = misura, ai = ev_FDI, n1i = n_FDI, ci = ev_FCM, n2i = n_FCM, data = d)
}

# Scelta del modello principale (protocollo §11 e deviazione §15 del 2026-09-29):
# - S5–S8: Mantel-Haenszel;
# - P1–S3: REML + HKSJ, ma Mantel-Haenszel se le celle zero escluderebbero trial dal REML;
# - se un braccio non ha eventi in nessun trial, il RR non è definito: Peto OR e RD (MH);
# - se meno di 2 trial hanno eventi, nessuna misura relativa è aggregabile: solo la RD,
#   che comprende i trial a doppio zero (§11).
non_doppio_zero <- function(d) d[!(d$ev_FDI == 0 & d$ev_FCM == 0), ]
scelta <- function(d, e) {
  dn <- non_doppio_zero(d)
  if (nrow(dn) < K_MIN) return("rd")
  if (sum(dn$ev_FDI) == 0 || sum(dn$ev_FCM) == 0) return("peto+rd")
  if (e %in% RARI) return("mh")
  if (any(dn$ev_FDI == 0 | dn$ev_FCM == 0 | dn$ev_FDI == dn$n_FDI | dn$ev_FCM == dn$n_FCM)) return("mh")
  "reml"
}
MODELLI <- list(
  reml = list(nome = "REML + HKSJ, senza correzione", misura = "RR", f = function(d) reml_rr(d),
              dati = function(d) d[d$ev_FDI > 0 & d$ev_FCM > 0 & d$ev_FDI < d$n_FDI & d$ev_FCM < d$n_FCM, ]),
  mh   = list(nome = "MH effetti fissi, senza correzione", misura = "RR", f = function(d) mh(d, "RR"),
              dati = non_doppio_zero),
  peto = list(nome = "Peto", misura = "OR", dati = non_doppio_zero,
              f = function(d) { d <- non_doppio_zero(d); if (nrow(d) < K_MIN) NULL else
                rma.peto(ai = ev_FDI, n1i = n_FDI, ci = ev_FCM, n2i = n_FCM, data = d) }),
  rd   = list(nome = "MH effetti fissi, doppi zeri inclusi", misura = "RD", f = function(d) mh(d, "RD"),
              dati = function(d) d)
)
codici <- function(sc) if (sc == "peto+rd") c("peto", "rd") else sc
esegui <- function(d, e, f, cod, etichetta_analisi, forest_file = NULL) {
  m <- MODELLI[[cod]]
  x <- prova(m$f(d))
  if (is.null(x) || fallito(x)) {
    aggiungi(d, e, f, etichetta_analisi, m$nome, m$misura,
             nota = if (fallito(x)) as.character(x) else sprintf("non stimabile: %d trial utilizzabili", nrow(m$dati(d))))
    return(invisible(NULL))
  }
  aggiungi(d, e, f, etichetta_analisi, m$nome, m$misura, x)
  if (etichetta_analisi == "principale") completa_principale(x, m$dati(d), e, f, m$misura)
  # un forest plot non disegnabile (es. RD con tutti i bracci a zero eventi) non ferma l'analisi
  if (!is.null(forest_file)) prova(forest_png(x, m$dati(d), forest_file,
                                              sprintf("%s, finestra %s — %s", e, f, m$nome), m$misura))
}

# Per il risultato principale (GRADE, guida 99-Meta/grade-meta.md §3-4): trial e
# partecipanti effettivamente nel modello, pesi dei trial ed effetti assoluti per
# 1000. Rischio con FCM = rischio grezzo aggregato dei bracci FCM nel modello.
pesi <- list()
completa_principale <- function(fit, dd, e, f, misura) {
  i <- length(risultati)
  risultati[[i]]$trial <<- paste(dd$etichetta, collapse = "; ")
  risultati[[i]]$partecipanti <<- sum(dd$n_FDI + dd$n_FCM)
  w <- prova(weights(fit))
  if (!fallito(w)) pesi[[length(pesi) + 1]] <<- data.frame(
    esito = e, finestra = f, misura = misura, trial = dd$etichetta, trial_id = dd$trial_id,
    peso_pct = round(as.numeric(w), 1), rob = dd$rob, produttore = dd$produttore, stringsAsFactors = FALSE)
  if (misura == "MD") return(invisible(NULL))
  cr <- sum(dd$ev_FCM) / sum(dd$n_FCM)
  eff <- c(as.numeric(fit$b), fit$ci.lb, fit$ci.ub)
  risultati[[i]]$rischio_fcm_1000 <<- round(1000 * cr)
  if (misura == "RD") {
    # la RD è già assoluta: non si ricava un rischio FDI dal rischio grezzo FCM
    diff <- eff
  } else {
    fdi <- switch(misura, RR = cr * exp(eff), OR = exp(eff) * cr / (1 - cr + exp(eff) * cr))
    risultati[[i]]$rischio_fdi_1000 <<- round(1000 * fdi[1])
    diff <- fdi - cr
  }
  risultati[[i]]$diff_1000 <<- round(1000 * diff[1])
  risultati[[i]]$diff_1000_inf <<- round(1000 * diff[2])
  risultati[[i]]$diff_1000_sup <<- round(1000 * diff[3])
}

# Esiti descritti senza aggregare, per decisione dell'utente (deviazione §15)
NON_AGGREGARE <- c(
  S7 = "sintesi narrativa per eterogeneità clinica: definizioni diverse (Fishbane e orticaria vs «infusion-related reaction probably/highly probably related») ed effetti di direzione opposta; decisione dell'utente 2026-09-29"
)

forest_png <- function(fit, d, file, titolo, misura) {
  png(file, width = 2000, height = 350 + 110 * nrow(d), res = 200, type = "cairo")
  on.exit(dev.off())
  forest(fit, slab = d$etichetta, atransf = if (misura %in% c("RR", "OR")) exp else NULL,
         header = c("Trial", paste(misura, "[IC 95%]")), xlab = paste(misura, "FDI vs FCM"),
         main = titolo, cex = 0.8)
}

# Stime dei singoli trial, senza aggregazione (servono alle sintesi narrative e a GRADE)
singoli <- list()
for (i in which(dati$esito %in% DICOTOMICI)) {
  r <- dati[i, ]
  zero <- r$ev_FDI == 0 || r$ev_FCM == 0
  rr <- if (zero) c(NA, NA, NA) else {
    lr <- log((r$ev_FDI / r$n_FDI) / (r$ev_FCM / r$n_FCM))
    se <- sqrt(1 / r$ev_FDI - 1 / r$n_FDI + 1 / r$ev_FCM - 1 / r$n_FCM)
    exp(c(lr, lr - 1.959964 * se, lr + 1.959964 * se))
  }
  p1 <- r$ev_FDI / r$n_FDI; p2 <- r$ev_FCM / r$n_FCM
  se_rd <- sqrt(p1 * (1 - p1) / r$n_FDI + p2 * (1 - p2) / r$n_FCM)
  singoli[[length(singoli) + 1]] <- data.frame(
    esito = r$esito, finestra = r$finestra, trial = r$etichetta, trial_id = r$trial_id,
    eventi_fdi = sprintf("%d/%d", r$ev_FDI, r$n_FDI), eventi_fcm = sprintf("%d/%d", r$ev_FCM, r$n_FCM),
    rr = signif(rr[1], 4), rr_inf = signif(rr[2], 4), rr_sup = signif(rr[3], 4),
    rd = signif(p1 - p2, 4), rd_inf = signif(p1 - p2 - 1.959964 * se_rd, 4), rd_sup = signif(p1 - p2 + 1.959964 * se_rd, 4),
    rob = r$rob, sede_fdi = r$sede_FDI, sede_fcm = r$sede_FCM,
    nota = if (zero) "RR non definito senza correzione (zero eventi in un braccio); RD con IC di Wald" else "IC di Wald",
    stringsAsFactors = FALSE)
}
singoli <- do.call(rbind, singoli)
write.csv(singoli[order(singoli$esito, singoli$finestra, singoli$trial), ],
          file.path(OUT, "trial-singoli.csv"), row.names = FALSE, na = "")

for (ef in unique(paste(dati$esito, dati$finestra))) {
  e <- strsplit(ef, " ")[[1]][1]; f <- strsplit(ef, " ")[[1]][2]
  d <- dati[dati$esito == e & dati$finestra == f, ]
  d <- d[order(d$etichetta), ]

  if (e %in% DICOTOMICI) {
    con_eventi <- d[d$ev_FDI + d$ev_FCM > 0, ]
    if (e %in% names(NON_AGGREGARE)) {
      aggiungi(d, e, f, "principale", "sintesi narrativa", "RR", nota = NON_AGGREGARE[[e]])
      risultati[[length(risultati)]]$partecipanti <- sum(d$n_FDI + d$n_FCM)
      next
    }
    # §11: aggregazione solo con almeno K_MIN trial con dati;
    # §6.3: per S5 e S6 servono anche almeno K_MIN trial con almeno un evento
    if (nrow(d) < K_MIN || (e %in% ESITI_63 && nrow(con_eventi) < K_MIN)) {
      aggiungi(d, e, f, "principale", "sintesi narrativa", "RR",
               nota = if (nrow(d) < K_MIN) sprintf("%d trial con dati (< %d): nessuna stima aggregata", nrow(d), K_MIN)
                      else sprintf("%d trial con almeno un evento (< %d, protocollo §6.3): nessuna stima aggregata", nrow(con_eventi), K_MIN))
      risultati[[length(risultati)]]$partecipanti <- sum(d$n_FDI + d$n_FCM)
      next
    }
    # nessun evento in nessun trial: anche la RD è degenere (varianza nulla, IC [0; 0])
    if (nrow(con_eventi) == 0) {
      aggiungi(d, e, f, "principale", "sintesi narrativa", "RD",
               nota = sprintf("%d trial con dati e nessun evento in nessun braccio: effetto non stimabile", nrow(d)))
      risultati[[length(risultati)]]$partecipanti <- sum(d$n_FDI + d$n_FCM)
      next
    }
    sc <- scelta(d, e)
    for (cod in codici(sc))
      esegui(d, e, f, cod, "principale", file.path(OUT, "forest", sprintf("%s-%s-%s.png", e, f, cod)))
    # affiancati: gli altri modelli (§11: con k < 5 si mostrano insieme)
    for (cod in setdiff(c("reml", "mh"), codici(sc))) esegui(d, e, f, cod, "affiancato (k<5)")
    if (e %in% RARI || sc == "peto+rd") {
      for (cod in setdiff(c("rd", "peto"), codici(sc))) esegui(d, e, f, cod, paste0("sensibilità: ", MODELLI[[cod]]$nome))
      if (nrow(con_eventi) >= 3 && requireNamespace("lme4", quietly = TRUE)) {
        x <- prova(rma.glmm(measure = "OR", ai = ev_FDI, n1i = n_FDI, ci = ev_FCM, n2i = n_FCM,
                            data = con_eventi, model = "UM.FS"))
        if (!fallito(x)) aggiungi(con_eventi, e, f, "sensibilità: GLMM", "GLMM UM.FS", "OR", x)
        else aggiungi(con_eventi, e, f, "sensibilità: GLMM", "GLMM UM.FS", "OR", nota = as.character(x))
      }
    }
    x <- prova(reml_rr(d, add = 0.5))
    if (!is.null(x) && !fallito(x)) aggiungi(d, e, f, "sensibilità: correzione 0,5", "REML + HKSJ, 0,5 solo ai trial con zeri", "RR", x)
    x <- prova({dd <- d[d$ev_FDI > 0 & d$ev_FCM > 0, ]; if (nrow(dd) >= K_MIN)
      rma(measure = "RR", ai = ev_FDI, n1i = n_FDI, ci = ev_FCM, n2i = n_FCM, data = dd, method = "FE")})
    if (!is.null(x) && !fallito(x)) aggiungi(d, e, f, "sensibilità 2: effetti fissi IV", "inverso della varianza, effetti fissi", "RR", x)

    # sottogruppi esplorativi (§11): solo con almeno K_MIN trial per livello in almeno due livelli;
    # stima per livello con il modello principale e test di differenza fra le stime (Q fra gruppi)
    if (sc %in% c("reml", "mh")) {
      m <- MODELLI[[sc]]
      for (fattore in c("schema_dose", "popolazione")) {
        dd <- m$dati(d)
        dd$livello <- sottogruppi[[fattore]][match(dd$trial_id, sottogruppi$trial_id)]
        dd <- dd[!is.na(dd$livello) & dd$livello != "", ]
        livelli <- names(which(table(dd$livello) >= K_MIN))
        if (length(livelli) < 2) {
          aggiungi(d, e, f, paste0("sottogruppi: ", fattore), m$nome, m$misura,
                   nota = sprintf("non eseguibile: livelli con almeno %d trial: %s", K_MIN,
                                  if (length(livelli)) paste(livelli, collapse = ", ") else "nessuno"))
          next
        }
        stime <- list()
        for (lv in livelli) {
          x <- prova(m$f(dd[dd$livello == lv, ]))
          if (is.null(x) || fallito(x)) next
          aggiungi(dd[dd$livello == lv, ], e, f, paste0("sottogruppo: ", fattore, " = ", lv), m$nome, m$misura, x)
          stime[[lv]] <- c(b = as.numeric(x$b), se = as.numeric(x$se))
        }
        if (length(stime) >= 2) {
          b <- sapply(stime, `[`, "b"); w <- 1 / sapply(stime, `[`, "se")^2
          qb <- sum(w * (b - sum(w * b) / sum(w))^2)
          aggiungi(dd[dd$livello %in% names(stime), ], e, f, paste0("sottogruppi: test ", fattore), m$nome, m$misura,
                   nota = sprintf("Q fra gruppi = %.3f, gl = %d, p = %.3g", qb, length(stime) - 1,
                                  pchisq(qb, length(stime) - 1, lower.tail = FALSE)))
          risultati[[length(risultati)]]$q <- qb
          risultati[[length(risultati)]]$q_p <- pchisq(qb, length(stime) - 1, lower.tail = FALSE)
        }
      }
    }

    # sensibilità 1, 3, 4, 5 con lo stesso modello principale
    sottoinsiemi <- list(
      "sensibilità 1: solo RoB basso" = d$rob %in% "basso",
      "sensibilità 3: soglia esatta" = if (e %in% names(SOGLIA)) !is.na(d$soglia) & abs(d$soglia - SOGLIA[e]) < 1e-9 else rep(TRUE, nrow(d)),
      "sensibilità 4: senza produttore" = d$produttore %in% "nessuno",
      "sensibilità 5: senza dati solo da registro/abstract" =
        !vapply(strsplit(d$fonte_dato, "+", fixed = TRUE), function(v) all(v %in% FONTI_DEBOLI), logical(1))
    )
    for (s in names(sottoinsiemi)) {
      if (s == "sensibilità 3: soglia esatta" && !(e %in% names(SOGLIA))) next
      ds <- d[sottoinsiemi[[s]], ]
      for (cod in codici(sc)) {
        m <- MODELLI[[cod]]
        if (nrow(ds) == nrow(d)) { aggiungi(ds, e, f, s, m$nome, m$misura, nota = "nessun trial escluso: coincide con la principale"); next }
        # la RD richiede K_MIN trial con dati e almeno un evento; le misure relative K_MIN trial con eventi
        insufficiente <- if (cod == "rd") nrow(ds) < K_MIN || sum(ds$ev_FDI + ds$ev_FCM) == 0
                         else sum(ds$ev_FDI + ds$ev_FCM > 0) < K_MIN
        if (insufficiente) {
          aggiungi(ds, e, f, s, m$nome, m$misura, nota = sprintf("non stimabile: %d trial nel sottoinsieme", nrow(ds)))
          next
        }
        esegui(ds, e, f, cod, s)
      }
    }
  } else {
    # S4: differenza media in mmol/L
    d$yi_ok <- TRUE
    fitc <- function(dd, metodo) rma(measure = "MD", m1i = m_FDI, sd1i = sd_FDI, n1i = n_FDI,
                                     m2i = m_FCM, sd2i = sd_FCM, n2i = n_FCM, data = dd,
                                     method = metodo, test = if (metodo == "FE") "z" else "knha")
    if (nrow(d) < K_MIN) { aggiungi(d, e, f, "principale", "sintesi narrativa", "MD", nota = "meno di 2 trial"); next }
    x <- prova(fitc(d, "REML"))
    if (fallito(x)) aggiungi(d, e, f, "principale", "REML + HKSJ", "MD", nota = as.character(x))
    else {
      aggiungi(d, e, f, "principale", "REML + HKSJ", "MD", x)
      completa_principale(x, d, e, f, "MD")
      forest_png(x, d, file.path(OUT, "forest", sprintf("%s-%s-reml.png", e, f)),
                 sprintf("%s, finestra %s — MD in mmol/L, REML + HKSJ", e, f), "MD")
    }
    x <- prova(fitc(d, "FE")); if (!fallito(x)) aggiungi(d, e, f, "affiancato (k<5) / sens. 2", "inverso della varianza, effetti fissi", "MD", x)
    dv <- d[d$misura_continua == "variazione-da-basale", ]
    if (nrow(dv) < nrow(d)) {
      x <- if (nrow(dv) >= K_MIN) prova(fitc(dv, "REML")) else NULL
      if (is.null(x) || fallito(x)) aggiungi(dv, e, f, "sensibilità: solo variazione dal basale", "REML + HKSJ", "MD", nota = "meno di 2 trial")
      else aggiungi(dv, e, f, "sensibilità: solo variazione dal basale", "REML + HKSJ", "MD", x)
    }
  }
}

campi <- unique(unlist(lapply(risultati, names)))
ris <- do.call(rbind, lapply(risultati, function(r) {
  r[setdiff(campi, names(r))] <- NA
  as.data.frame(r[campi], stringsAsFactors = FALSE)
}))
for (c in c("stima", "ic_inf", "ic_sup", "pi_inf", "pi_sup", "tau2", "q")) ris[[c]] <- signif(ris[[c]], 4)
ris$p <- signif(ris$p, 3); ris$q_p <- signif(ris$q_p, 3); ris$i2 <- round(ris$i2, 1)
ris <- ris[order(ris$esito, ris$finestra), ]
write.csv(ris, file.path(OUT, "risultati.csv"), row.names = FALSE, na = "")
write.csv(esclusi, file.path(OUT, "esclusioni.csv"), row.names = FALSE, na = "")
write.csv(do.call(rbind, pesi), file.path(OUT, "pesi.csv"), row.names = FALSE, na = "")

# ---- registro della run -----------------------------------------------------
sink(file.path(OUT, "run.txt"))
cat("Meta-analisi FDI vs FCM — run dello script 50-Metanalisi/analisi.R\n\n")
cat("Commit HEAD:", commit, if (sporco) "(ATTENZIONE: script o 30-Dati con modifiche non committate)" else "", "\n")
cat("SHA-256 di 30-Dati/ma-bracci.csv:", checksum, "\n")
cat("Righe usate:", nrow(usati), "— combinazioni trial × esito × finestra analizzabili:", nrow(dati),
    "— escluse:", nrow(esclusi), "\n\n")
print(sessionInfo())
sink()

cat(sprintf("Scritti in %s: risultati.csv (%d righe), trial-singoli.csv, pesi.csv, input-analisi.csv, esclusioni.csv (%d), forest/, run.txt\n",
            OUT, nrow(ris), nrow(esclusi)))
