# SPEC.md — Arena di Bot Python (MVP) + Ambiente “Iterated Prisoner’s Dilemma”

## 0) Scopo (MVP)

Costruire un sito dove gli utenti:

1) si registrano / fanno login
2) vedono griglia con ambienti predefiniti.
3) creano e salvano **bot Python** con un **nome**
4) testano il bot in sandbox contro altri giocatori
5) inviano (“submit”) il bot per partite valutate
6) vedono **classifiche** e **replay** delle partite e **grafici** e **statistiche**.

**MVP = 1 ambiente**: Iterated Prisoner’s Dilemma (2 giocatori, ripetuto).

---

## 1) Glossario / Oggetti

- **User**: account con username/password hash.
- **Environment**: un gioco/simulazione. Bisogna definire un'interfaccia comune per gli environment.
- **Bot**: codice Python + metadata (nome bot, owner, versione).
- **Submission**: uno snapshot immutabile del bot.
- **Match**: una partita tra 2 submission, con seed e transcript.
- **Leaderboard**: ranking per environment.

---

## 2) Requisiti funzionali (MVP)

### 2.1 Auth & profilo

- Registrazione: username + password.
- Login.
- Pagina profilo: lista bot dell’utente, submission recenti, ultimi match.

### 2.2 Gestione Bot (salvataggio + nomi)

- L’utente può creare un bot con:
  - `name` (string, unico per utente; es. “tit_for_tat_v1”)
  - `description` (opzionale)
  - `code` (testo Python)

- Un bot può avere **più versioni**:
  - `Bot` (entità “logica” con nome)
  - `BotVersion` (snapshot di codice)

- Operazioni:
  - creare bot
  - rinominare bot
  - duplicare bot
  - salvare nuova versione
  - selezionare versione “attiva” per test
  - creare “Submission” (snapshot immutabile) da una versione

### 2.3 Esecuzione locale (sandbox test)

- L’utente può premere **Run Test**:
  - esegue 1 match vs baseline (es. “always_cooperate”)
  - mostra log e transcript
  - NON altera rating globale

### 2.4 Submit + ranked evaluation

- Submit crea una Submission immutabile:
  - status: `queued | evaluating | ranked | failed`

- Valutazione ranked (MVP):
  - giocare N match contro set fisso di anchor/baseline + matchmaking semplice
  - aggiornare rating Elo dopo completamento batch iniziale

### 2.5 Replay / Match viewer

- Ogni match salva:
  - seed
  - payoff matrix
  - lista step: obs_p1, act_p1, obs_p2, act_p2, reward, cumulative score

- UI replay:
  - timeline per round
  - riassunto finale + link condivisibile (solo read)

### 2.6 Leaderboard

- Classifica per environment, mostra:
  - rating Elo
  - #match
  - win/draw/loss
  - link alla submission

---

## 3) Ambiente MVP: Iterated Prisoner’s Dilemma (IPD)

### 3.1 Setup

- 2 giocatori: P1, P2
- Numero round: `ROUNDS = 200` (fisso, deterministico)
- Azioni possibili: `"C"` (cooperate) o `"D"` (defect)

### 3.2 Payoff matrix (standard)

- (C, C) => (3, 3)
- (D, C) => (5, 0)
- (C, D) => (0, 5)
- (D, D) => (1, 1)

### 3.3 Observation schema (per round t, 1-indexed)

Ogni bot riceve un dict JSON-serializzabile:

```json
{ "round": 17, "max_rounds": 200, "history": [('D', 'D'), ...] }
````

### 3.4 Action schema

Il bot deve ritornare una stringa:

- `"C"` oppure `"D"`

Qualsiasi altro output è “invalid action”.

---

## 4) API Bot (contratto Python)

Ogni submission deve esporre una funzione:

```python
def act(observation: dict, state: dict) -> tuple[str, dict]:
    """
    observation: dict (vedi schema IPD)
    state: dict mutabile, usato come memoria persistente tra round (serializzabile)

    ritorna: (action, new_state)
    """
    return "C", state
```

Regole:

- `state` deve rimanere JSON-serializzabile (dict/list/int/float/str/bool/null).
- `act()` deve essere pura rispetto all’esterno: niente rete, niente filesystem persistente.
- Se `state` non serializzabile -> submission invalid per quel match.

---

## 5) Error handling in match

- **Invalid action**: forfeit e il bot viene ritirato.
- **Exception in act()**: forfeit e si logga stacktrace.
- **Timeout** (vedi §6): => **forfeit** (match perso).

---

## 6) Sandboxing + limiti (minimo indispensabile)

Obiettivo: eseguire codice non fidato con rischio basso.

### 6.1 Isolamento processo

- Eseguire i bot in un processo separato per match, idealmente container Docker.
- Impostazioni minime container:
  - filesystem read-only
  - working dir temporanea `/tmp` (scrivibile) con quota
  - **no network** (nessuna uscita/ingresso)
  - user non-root
  - limiti risorse (cgroups): memoria, cpu

### 6.2 Limiti runtime

- **Per chiamata act()**
  - timeout wall-clock: `MAX_STEP_MS = 30ms`
- **Per match**
  - timeout totale: `MAX_MATCH_MS = 3000ms` (o CPU quota equivalente)
- Memoria: `MAX_MEM_MB = 256MB`
- Output log (stdout/stderr) limitato: `MAX_LOG_KB = 64KB` per match

### 6.3 Restrizioni Python (minimo)

- Avviare python in modalità isolata (es. `python -I`) e senza env user.
- Consentire solo stdlib + eventuale `numpy`.
- Bloccare import pericolosi (best-effort):
  - vietati: `socket`, `subprocess`, `os` (o sottoinsiemi), `pathlib` scrittura oltre /tmp

- in MVP: soluzione pragmatica = non installare pacchetti extra, no network, FS read-only

> Nota: il vero hardening richiede policy più forti (seccomp/apparmor). Per MVP: Docker no-network + read-only + limiti + non-root è accettabile.

---

## 7) Valutazione ranked (MVP)

### 7.1 Anchor bots (predefiniti)

- `always_cooperate`
- `always_defect`
- `tit_for_tat`
- `random_50_50` (deterministico via seed)

### 7.2 Batch iniziale (placement)

Quando una submission entra in ranked:

- Giocare `N=40` match totali:
  - 10 vs ciascun anchor (seed deterministici)
- Calcolare Elo iniziale e incertezza (anche solo “provisional” flag).

---

## 8) Database (schema suggerito, minimo)

- `users(id, username, password_hash, created_at)`
- `bots(id, user_id, name, description, created_at, updated_at)`
- `bot_versions(id, bot_id, version_num, code, created_at)`
- `submissions(id, bot_version_id, status, created_at, error_log)`
- `matches(id, env_id, submission_a, submission_b, seed, status, started_at, finished_at)`
- `match_steps(id, match_id, round, obs_a, act_a, obs_b, act_b, reward_a, reward_b, cum_a, cum_b)`
- `ratings(submission_id, env_id, elo, games, wins, draws, losses, updated_at)`

---

## 9) UI (pagine MVP)

- `/login`, `/register`
- `/env/ipd`:
  - descrizione gioco + spec obs/action
  - leaderboard
  - bottone “create bot”
- `/bots`:
  - lista bot dell’utente (con nome)
  - create/rename/duplicate
- `/bots/{bot_id}`:
  - editor codice
  - selezione versione
  - Run Test (sandbox)
  - Submit
- `/submissions/{id}`:
  - stato evaluation
  - rating + stats
  - match list
- `/matches/{id}`:
  - replay step-by-step

---

## 10) Criteri di accettazione (MVP)

- Un utente può creare 2 bot con nomi diversi, salvarli, vederli in lista.
- Un bot può essere testato in sandbox: match vs baseline con replay.
- Un submit produce una submission immutabile e parte la valutazione.
- Leaderboard mostra la submission con Elo aggiornato dopo placement.
- Timeout ed errori sono gestiti senza crash del server e sono visibili nei log.
