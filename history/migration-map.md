# Migração — Legado → Novo

> Mapeamento de cada script antigo para o módulo novo. As pastas legadas são **read-only** (consulta histórica).

## Backend (lógica)

| Script legado | Substituto | Notas |
|---|---|---|
| `regionalizador.py` (v1) | `services/clustering.py::build_regions` | KMeans + atributos, sem filtro geográfico |
| `regionalizadoarc.py` | **deletado** | Dependia de ArcGIS (proibido) |
| `prototipo.py` (Streamlit) | `app/main.py` (API) | Streamlit descartado; UI agora é Next.js |
| `prototipofinal.py` | `app/main.py` + `services/clustering.py` | Refatorado em classe FastAPI + services |
| `prototipobeta.py` | `services/clustering.py::build_regions` | Convex hull + max_raio implementados em `build_regions` |
| `reg.py` (regionalização2_0) | `services/clustering.py` | Validação de capacidade, rebalanceamento |
| `reg2.py` (regionalização2_0) | `services/clustering.py` | Mesmo, com interface Tkinter → FastAPI |
| `reg.py` (bairros.xlsx) | `services/geography.py::filter_points_within_city` | Reclassificação por ponto-em-polígono |
| `processar_bairros.py` | `services/geography.py` | Duplicado, descontinuado |
| `geocoding.py` | `services/geocoding.py` (reescrito) | Sem ArcGIS; AwesomeAPI + Nominatim com cache |
| `geocoding2.py` | `services/geocoding.py` | Mesma reescrita |
| `geocoding3.py` | `services/geocoding.py` | Mesma reescrita (com cache + rate limit) |
| `criador_raio.py` | `services/exporter.py::export_to_kml` | Buffer geodésico integrado ao KML |
| `quebra_regioes.py` | `services/exporter.py::export_to_xlsx` | 1 XLSX com coluna Região, não N arquivos |
| `extraReg.py` | `services/exporter.py` | KML gerado direto, sem passo intermediário |
| `converte_camada.py` | `services/exporter.py` | ExtendedData do KML inclui região+participantes |

## Dados
| Ativo legado | Substituto |
|---|---|
| `RJ_Municipios_2022.*` (SHP) | Upload pelo usuário em cada job |
| `Indicações_RJ_Teste.xlsx` | Upload pelo usuário |
| `participantes_rj.xlsx` | Upload pelo usuário |
| `bairros.xlsx` | Removido (geocoding agora é serviço, não arquivo) |
| `API_KEY ArcGIS` (vários arquivos) | **NUNCA MAIS** — Nominatim é gratuito |

## UI
| Componente legado | Substituto |
|---|---|
| Tkinter `root.mainloop()` | Next.js `app/page.tsx` |
| Botões `tk.Button` | shadcn `<Button>` |
| `status_label.config(text=...)` | shadcn `<Progress>` + `<StatusBadge>` + Sonner toasts |
| `filedialog.askopenfilename` | `<Input type="file">` no form |
| `threading.Thread` (Tkinter) | FastAPI `BackgroundTasks` (servidor) |

## Saída
| Formato legado | Substituto |
|---|---|
| `regioes.xlsx` | `regionalizacao_regioes.xlsx` |
| `escolas_regionalizadas.xlsx` | `regionalizacao_escolas.xlsx` |
| `participantes_regionalizados.xlsx` | `regionalizacao_participantes.xlsx` |
| `regioes.kml` | `regioes.kml` (mantido) |
| `regioes.shp` / `escolas_regionalizadas.shp` | Removido (XLSX + KML cobrem o caso) |
| `resultado.geojson` | Acrescentado (frontend pode ler direto) |

## Removido (sem substituto)
- `regionalizadoarc.py` (ArcGIS Location-Allocation) — não há equivalente open-source simples; o problema pode ser resolvido com k-medoids + restrição de capacidade (spec futura).
