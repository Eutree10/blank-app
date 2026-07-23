import type { Problem } from '../types'

// ---------------------------------------------------------------------------
// DATASET DE MUESTRA — Nivel 2
//
// La política de red del entorno de desarrollo bloquea oma.org.ar, por lo que
// no fue posible scrapear los enunciados oficiales automáticamente. Estos
// problemas son de MUESTRA (marcados con `muestra: true`): sirven para probar
// toda la lógica de la app (asignación diaria, random sin repetición, historial
// y progreso) desde el primer minuto.
//
// Para cargar los problemas OFICIALES de OMA:
//   1. Corré `python scripts/scrape_oma.py` en una red con acceso a oma.org.ar
//      (genera public/oma-nivel2.json).
//   2. En la app: pestaña "Datos" -> Importar JSON, o pegá el contenido.
// El import REEMPLAZA este dataset conservando tu historial de completados por id.
// ---------------------------------------------------------------------------

const FUENTE = 'Muestra (reemplazar por enunciado oficial de OMA — oma.org.ar/enunciados)'

function P(
  instancia: 'Intercolegial' | 'Zonal',
  anio: number,
  numero: number,
  enunciado: string,
): Problem {
  return {
    id: `${instancia}-${anio}-N2-P${numero}`,
    anio,
    instancia,
    nivel: 2,
    numero,
    enunciado,
    fuente: FUENTE,
    muestra: true,
  }
}

export const seedProblems: Problem[] = [
  // ===================== INTERCOLEGIAL (año completo por día) =====================
  // 2016
  P('Intercolegial', 2016, 1, 'En un número de tres cifras, la cifra de las centenas es el doble de la de las unidades y la de las decenas es la suma de las otras dos. Hallá todos los números que cumplen esto.'),
  P('Intercolegial', 2016, 2, 'Un rectángulo tiene perímetro 34 y sus lados miden números enteros. ¿Cuál es la mayor área posible? ¿Y la menor?'),
  P('Intercolegial', 2016, 3, 'Se reparten 100 caramelos entre tres chicos de modo que cada uno reciba al menos 20 y todos reciban cantidades distintas. ¿De cuántas maneras puede hacerse si además el mayor recibe exactamente 40?'),
  // 2017
  P('Intercolegial', 2017, 1, 'Ana escribe los números del 1 al 50. ¿Cuántas veces escribe la cifra 3 en total?'),
  P('Intercolegial', 2017, 2, 'En un triángulo, dos de sus ángulos miden 40° y 75°. Se traza la bisectriz del tercer ángulo. ¿En qué dos ángulos queda dividido ese tercer ángulo?'),
  P('Intercolegial', 2017, 3, 'Un número es "capicúa" si se lee igual de izquierda a derecha que al revés. ¿Cuántos capicúas de 4 cifras son múltiplos de 5?'),
  // 2018
  P('Intercolegial', 2018, 1, 'La suma de tres números consecutivos es 2018 más que el menor de ellos. Hallá los tres números.'),
  P('Intercolegial', 2018, 2, 'Un cuadrado de lado 12 se divide en cuadraditos de lado 3. Se pintan de gris los cuadraditos de la diagonal. ¿Qué fracción del cuadrado grande quedó pintada?'),
  P('Intercolegial', 2018, 3, 'Se tienen fichas numeradas del 1 al 9. ¿De cuántas maneras se pueden elegir tres fichas cuya suma sea múltiplo de 3?'),
  // 2019
  P('Intercolegial', 2019, 1, 'Un reloj atrasa 3 minutos cada hora. Si se pone en hora a las 08:00, ¿qué hora marcará el reloj cuando la hora real sea 20:00 del mismo día?'),
  P('Intercolegial', 2019, 2, 'El promedio de cinco números enteros positivos distintos es 10. ¿Cuál es el mayor valor posible del mayor de ellos?'),
  P('Intercolegial', 2019, 3, 'En una cuadrícula de 4×4 se colorean algunas casillas de modo que cada fila y cada columna tenga exactamente dos casillas coloreadas. ¿Cuántas casillas se colorean en total?'),

  // =========================== ZONAL (2 problemas por día) ===========================
  // 2016
  P('Zonal', 2016, 1, 'Hallá todos los números naturales n tales que n + 12 es múltiplo de n.'),
  P('Zonal', 2016, 2, 'En el pizarrón están escritos los números del 1 al 20. En cada paso se borran dos números y se escribe su suma. Después de varios pasos queda un solo número. ¿Cuál es?'),
  P('Zonal', 2016, 3, 'Un cubo de arista 4 se pinta por fuera y luego se corta en cubitos de arista 1. ¿Cuántos cubitos tienen exactamente dos caras pintadas?'),
  P('Zonal', 2016, 4, 'María tiene monedas de 1, 2 y 5 pesos. ¿De cuántas formas puede pagar exactamente 10 pesos?'),
  P('Zonal', 2016, 5, 'El ángulo A de un triángulo isósceles mide 100°. Hallá la medida de los otros dos ángulos.'),
  // 2017
  P('Zonal', 2017, 1, '¿Cuál es el menor número natural que al dividirlo por 4, por 5 y por 6 deja siempre resto 1?'),
  P('Zonal', 2017, 2, 'En una fiesta cada persona saluda con la mano a todas las demás exactamente una vez. Si hubo 45 saludos, ¿cuántas personas había?'),
  P('Zonal', 2017, 3, 'Un rectángulo de 8×6 se corta en dos partes iguales con un solo corte recto que pasa por su centro. ¿Cuánto puede medir, como máximo, ese corte?'),
  P('Zonal', 2017, 4, 'Se escriben todos los números de 1 a 1000. ¿Cuántos de ellos NO contienen la cifra 7?'),
  P('Zonal', 2017, 5, 'La suma de dos números es 60 y su diferencia es 14. Hallá el producto de esos dos números.'),
  // 2018
  P('Zonal', 2018, 1, 'Un tanque se llena con la canilla A en 6 horas y con la canilla B en 4 horas. ¿En cuánto tiempo se llena usando las dos canillas a la vez?'),
  P('Zonal', 2018, 2, '¿Cuántos divisores positivos tiene el número 360?'),
  P('Zonal', 2018, 3, 'En un tablero de 3×3 se escriben los números del 1 al 9 (uno por casilla) de modo que la suma de cada fila sea la misma. ¿Cuánto vale esa suma?'),
  P('Zonal', 2018, 4, 'Un ciclista recorre la primera mitad de un camino a 20 km/h y la segunda mitad a 30 km/h. ¿Cuál es su velocidad promedio en todo el recorrido?'),
  P('Zonal', 2018, 5, 'Se eligen tres vértices distintos de un hexágono regular. ¿Cuántos de los triángulos que se forman son equiláteros?'),
  // 2019
  P('Zonal', 2019, 1, 'El producto de las cifras de un número de dos cifras es 24 y la suma de sus cifras es 11. ¿Cuál es el número?'),
  P('Zonal', 2019, 2, 'De un grupo de 30 alumnos, 18 practican fútbol y 15 practican básquet. Si 5 no practican ninguno, ¿cuántos practican ambos?'),
  P('Zonal', 2019, 3, 'Hallá el área de la región sombreada: un cuadrado de lado 10 con un círculo inscripto (usá π ≈ 3,14). ¿Cuánto mide el área que queda fuera del círculo?'),
  P('Zonal', 2019, 4, 'Se suman todos los números impares desde 1 hasta 99. ¿Cuál es el resultado?'),
  P('Zonal', 2019, 5, 'Un número de tres cifras es igual a 37 veces la suma de sus cifras. Hallá todos los números que cumplen esa condición.'),
]
