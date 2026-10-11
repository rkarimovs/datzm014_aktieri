# Aktieru nolīgšana (Talent Scheduling) ar Simulated Annealing

Praktiskais darbs kursā "Praktiskā kombinatoriālā optimizācija".

Filmai ir jānofilmē vairākas ainas, katrā ainā piedalās noteikti aktieri. Aktieris
tiek nolīgts no savas pirmās ainas līdz pēdējai, un alga jāmaksā par visām šī
perioda dienām, arī par dienām, kad viņš tikai gaida. Jāatrod ainu secība ar
mazākajām kopējām algu izmaksām. Uzdevums risināts ar Simulated Annealing, kas
implementēts Python valodā, izmantojot tikai standarta bibliotēku.

## Faili

```
talent/instance.py     uzdevuma dati, .dzn failu lasīšana un rakstīšana
talent/evaluation.py   mērķa funkcija
talent/sa.py           Simulated Annealing
talent/exact.py        precīzs DP risinātājs (tikai etalona optimumu iegūšanai)
talent/generator.py    testa piemēru ģenerators
instances/published/   literatūras piemēri (CSPLib prob039, MiniZinc benchmarks)
instances/generated/   ģenerētie piemēri, 16-80 ainas, viena aina dienā
results/               etalona vērtības un testēšanas rezultāti
solve.py               viena piemēra risināšana
compute_reference.py   etalona vērtību aprēķins
run_tests.py           eksperimenti
tests.py               pārbaudes
```

## Palaišana

Vajadzīgs Python 3.8 vai jaunāks, papildu bibliotēkas nav vajadzīgas.

```
python solve.py instances/published/film1.dzn
python solve.py instances/generated/gen_s40_a15.dzn --seed 3 --iters 200000
python tests.py
python compute_reference.py
python run_tests.py
```

`solve.py` izvada izmaksas, novirzi no etalona, ainu secību un grafiku, kur
`X` nozīmē, ka aktieris filmējas, `-` ka gaida (un saņem algu), `.` ka nav nolīgts.

## Testa piemēri

- rehearsal, film1, film2 no CSPLib prob039, publicētie optimālie gaidīšanas izmaksu
  lielumi ir 17, 146 un 87; DP risinātājs tos iegūst tādus pašus.
- MobStory un film103-film119 no MiniZinc benchmarks, optimums aprēķināts ar DP.
- gen_s16_a8, gen_s20_a10, gen_s24_a12, optimums aprēķināts ar DP.
- gen_s30_a12, gen_s40_a15, gen_s60_a20, gen_s80_a20, labākais zināmais rezultāts
  no visiem SA palaidieniem (`results/reference.json`).

Rezultātu kopsavilkums ir failā `results/summary.md`.

## Literatūra

- T. C. E. Cheng, J. E. Diamond, B. M. T. Lin. Optimal scheduling in film production to
  minimize talent hold cost. Journal of Optimization Theory and Applications 79(3), 1993.
- M. Garcia de la Banda, P. J. Stuckey, G. Chu. Solving talent scheduling with dynamic
  programming. INFORMS Journal on Computing 23(1), 2011.
- CSPLib prob039: https://www.csplib.org/Problems/prob039/
- MiniZinc benchmarks: https://github.com/MiniZinc/minizinc-benchmarks
