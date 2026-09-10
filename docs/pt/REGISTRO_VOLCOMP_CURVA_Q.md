# REGISTRO — curva q do volcomp contra o `ink_9um` [medido]

> **Superado em 2026-09-10.** A curva abaixo foi medida com offset de rótulo
> quantizado em 4 voxels (40, 40 em vez de 39, 39), gate reprovado (r = 0,944)
> e render de polaridade invertida em relação ao volume oficial. Os três
> defeitos foram corrigidos e a medida refeita; ver a ERRATA em
> `REGISTRO_VOLCOMP_INK.md`. As perdas relativas mudaram pouco (q = 8: 20,2 %
> para 21,9 %), mas os valores absolutos abaixo não devem ser citados.

Data: 2026-09-08. Prereg `93ab53cb…`. Scripts `metric/volcomp/{codifica_q,mede_curva_q}.py`.
Controle: chunk 42/34/26 codificado localmente em q = 8 contra o shard
publicado: MAE 0,000. Encoder local e volumes publicados são o mesmo codec.

Mesma região (4 952 chunks ao redor da malha oficial do w043), mesmo render
(28 fatias, nível 0), mesma inferência, mesmo rótulo (grade nativa, offset
(40, 40)), polaridade reverse (a que lê nestes renders).

| q | taxa | razão | d' | Δrazão | Δd' | passa (ambos) |
|---|---|---|---|---|---|---|
| 1 (original) | 1,0× | 2,408 | 1,596 | | | |
| 2 | 11,0× | 2,233 | 1,560 | −0,176 | −0,036 | não |
| 4 | 17,8× | 2,194 | 1,512 | −0,214 | −0,083 | não |
| 8 | 44,0× | 1,800 | 1,274 | −0,608 | −0,322 | não |
| 16 | 53,5× | 1,494 | 0,972 | −0,914 | −0,624 | não |

MAE amostral por q: 1,9 / 2,9 / 3,5 / 6,3.

## Veredito pelo §Critérios

Nenhum q ≥ 2 satisfaz |Δrazão| ≤ 0,05 **e** |Δd'| ≤ 0,10. Monotônico, sem
ponto suspeito.

## Leitura

- As duas métricas discordam até q = 4: d' (separabilidade) fica dentro do
  limiar (−0,04, −0,08); a razão de medianas cai 7–9 %. O detector separa
  quase igual, com menos contraste.
- Joelho entre q = 4 e q = 8: Δrazão triplica (−0,21 → −0,61), Δd' quadruplica.
- R1: q = 2 e q = 4 mantêm as linhas de texto no reverse; q = 16 apagado.
- O custo por taxa: q = 2 dá 11× com perda pequena em d'; q = 8 dá 44× com um
  quarto da separação. A escolha é de quem usa; o registro dá a curva.

## Ressalvas

Uma volta, um rolo, um checkpoint. O w043 é o segmento de referência do time
para o 9 µm, mas não é lei. Modelos 3D e de superfície não foram testados.
