# Tombola Natalizia
## Requisiti
- Python **>=3.12+** con `tkinter`
- Libreria `pillow` installata (non obbligatoria)

## Uso
```
python3 tombola.py
```
- Sposta la finestra di proiezione sul proiettore e premi **F11** per il fullscreen.
- Scegli il premio in palio (ambo, terna, ...) con i bottoni in alto: compare anche in proiezione.
- **Modalità manual**: clicca sul PC il numero uscito → animazione in proiezione, poi tabella.
- **Modalità auto**: premi *Estrai* (o barra spaziatrice), il programma sceglie a caso.
- **Aggiunta silenziosa**: con la spunta attiva, un clic aggiunge il numero senza animazione (solo in manuale).
- **Annulla ultimo** rimuove l'ultimo numero; **Sfondo on/off** mostra/nasconde `background.png` o `background.jpg` (stessa cartella da cui lanci lo script). La prossima estrazione con animazione toglie lo sfondo.

## Config (`tombola_config.json`, creato al primo avvio)
| Chiave | Significato | Default |
|---|---|---|
| `mode` | `"manual"` (clicchi i numeri) o `"auto"` (estrae il programma) | `"manual"` |
| `numbers` | quantità di numeri sullo schermo | `100` |
| `show_prize` | mostra in proiezione per cosa si gioca | `True` |
| `animation_ms` | quanto resta in grande il numero estratto (ms) | `5000` |
| `snow` | neve sul proiettore (`true`/`false`) | `False` |
| `projector_geometry` | `LxA+X+Y` della finestra di proiezione; X = larghezza del monitor principale | `1280x720+0+0` |
| `projector_fullscreen` | avvia la proiezione già a schermo intero | `False` |

## Salvataggio e ripristino
Ogni estrazione aggiorna `runs/tombola_AAAA-MM-GG_HH-MM-SS.json`. Dopo un crash, al riavvio il programma propone di riprendere l'ultima partita; in alternativa usa *Carica...*.

## Risoluzione dei problemi
La finestra "Proiezione" non compare: `projector_geometry` in `tombola_config.json` è probabilmente sbagliato, prova altre risoluzioni o posizioni