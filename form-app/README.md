# Form — App de calistenia por progresiones

Prototipo interactivo de alta fidelidad de **Form**, una app móvil (iPhone) para aprender y
dominar habilidades de calistenia mediante progresiones claras, entrenamientos personalizados
y seguimiento visual del progreso.

Es un único archivo autónomo (`index.html`) — HTML, CSS y JS embebidos, sin dependencias de
build. Se abre directamente en cualquier navegador y funciona sin conexión.

## Cómo verlo

```
open form-app/index.html      # macOS
xdg-open form-app/index.html  # Linux
```

O arrastrá el archivo al navegador. El prototipo se muestra dentro de un marco de iPhone y es
navegable con clics.

## Recorrido del prototipo

1. **Onboarding** — bienvenida, "cómo funciona" en 4 pasos y un cuestionario de 8 preguntas
   (nivel, frecuencia, lugar, equipamiento, habilidades, repeticiones, molestias, tiempo por
   sesión) que genera un plan.
2. **Hoy** — sesión recomendada del día (habilidad, duración, ejercicios, objetivo y
   `Comenzar sesión`), progreso semanal y próximas habilidades por desbloquear.
3. **Habilidades** — biblioteca por categorías (Empuje, Tirón, Equilibrio, Core, Piernas,
   Estáticas, Dinámicas) con búsqueda, filtros y estado (activa / disponible / bloqueada).
4. **Detalle de habilidad** — abrí **Handstand** para ver la ruta de progresión completa
   (`Wall plank → Wall walk → … → Handstand libre 30s`) con progresiones completadas, la
   actual destacada y las siguientes visibles pero bloqueadas. Tocá la progresión actual
   para ver video, técnica, errores frecuentes, series, requisitos y ejercicios de asistencia.
5. **Sesión** — reproductor de entrenamiento por fases (calentamiento → movilidad → técnica →
   progresión principal → fuerza → complementario → vuelta a la calma) con temporizador de
   descanso, registro de series y celebración al desbloquear una progresión.
6. **Progreso** — récords, evolución de repeticiones y aguante (gráficos), calendario de
   sesiones y totales.
7. **Perfil** — nivel general, habilidades favoritas, objetivos activos, equipamiento y ajustes
   (plan, recordatorios, Apple Health, modo sin conexión).

## Sistema de diseño

Interfaz clara, atlética, minimalista y premium — sin degradados excesivos, colores neón ni
fondos oscuros en la app (salvo el reproductor de sesión, que usa un modo inmersivo oscuro y
enfocado, al estilo Nike Training Club / Apple Fitness).

| Rol | Valor |
|---|---|
| Fondo | `#F6F5F2` (blanco cálido) |
| Superficie | `#FFFFFF` |
| Texto | `#16151A` (carbón) |
| Acento (rojo deportivo profundo) | `#D62B2B` |
| Éxito / progresión superada (funcional) | `#2E9E63` |
| Bloqueado | gris `#C4C1BB` |

- **Tipografía:** Inter (títulos compactos y fuertes; jerarquía restringida). Numerales,
  métricas y temporizadores en **JetBrains Mono** para que los dígitos queden alineados.
- **Acento reservado** para la acción principal y estados activos; el resto vive en la rampa
  de grises. El verde se usa solo como indicador funcional (progresión superada).
- **Iconografía** lineal y consistente. Las habilidades se identifican con siluetas corporales
  minimalistas dibujadas en SVG (placeholder de las fotos/videos reales del producto final).
- **Micro-animaciones** sutiles al completar una serie, desbloquear una progresión y al entrar
  a cada pantalla.
- Máximo de 4 secciones en la barra inferior; una acción principal destacada por pantalla.

> Las siluetas y "videos" son marcadores de posición del prototipo. En producción se
> reemplazan por fotografías o videos demostrativos reales.
