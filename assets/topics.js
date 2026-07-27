/* Banco de temas de la ruleta.
   t = tema · c = categoría · h = gancho · d = de qué va · q = por dónde empezar a investigar */

const TOPICS = [
  // ── Ciencia ─────────────────────────────────────────────────────────────
  {
    t: "Cristales de tiempo",
    c: "Ciencia",
    h: "Materia que se repite en el tiempo igual que un cristal se repite en el espacio.",
    d: "Un cristal normal ordena sus átomos en un patrón que se repite en el espacio. Frank Wilczek propuso en 2012 que podría existir materia cuyo patrón se repite en el tiempo: oscila para siempre en su estado de mínima energía, sin gastar nada. Se creía imposible; en 2016 se fabricaron los primeros en laboratorio y hoy se estudian dentro de procesadores cuánticos.",
    q: [
      "¿Por qué no viola esto la conservación de la energía ni el segundo principio?",
      "Diferencia entre un cristal de tiempo discreto y uno continuo",
      "Qué papel juegan en la memoria de los ordenadores cuánticos"
    ]
  },
  {
    t: "El reactor nuclear de Oklo",
    c: "Ciencia",
    h: "Hace 1.700 millones de años, la Tierra encendió sola un reactor nuclear y lo mantuvo 200.000 años.",
    d: "En 1972, en una mina de uranio de Gabón, un análisis rutinario dio una anomalía: al mineral le faltaba uranio-235. La explicación era que un yacimiento se había vuelto crítico por sí mismo, moderado por agua subterránea, y había funcionado en pulsos durante milenios. Hoy Oklo se usa para estudiar si las constantes de la física cambian con el tiempo.",
    q: [
      "¿Por qué hoy sería imposible que ocurriera de nuevo?",
      "Cómo se autorregulaba con el agua (ciclos de ebullición)",
      "Qué aporta Oklo al almacenamiento de residuos nucleares"
    ]
  },
  {
    t: "Sonoluminiscencia",
    c: "Ciencia",
    h: "Una burbuja atrapada en sonido colapsa y emite un destello de luz más caliente que la superficie del Sol.",
    d: "Si atrapas una burbuja de aire en agua con ondas ultrasónicas, la burbuja se expande y colapsa miles de veces por segundo. En cada colapso emite un flash de luz de picosegundos, con temperaturas estimadas de decenas de miles de grados. El mecanismo exacto sigue discutiéndose desde 1934.",
    q: [
      "Qué teorías compiten para explicar el destello (plasma, ondas de choque)",
      "Por qué se llegó a proponer la 'fusión por burbujas' y cómo acabó",
      "El camarón pistola y la luz que produce al disparar"
    ]
  },
  {
    t: "El efecto Mpemba",
    c: "Ciencia",
    h: "En ciertas condiciones, el agua caliente se congela antes que la fría. Nadie se pone de acuerdo en por qué.",
    d: "Lo describió Aristóteles y lo redescubrió en 1963 un estudiante tanzano, Erasto Mpemba, haciendo helado. Durante décadas se propusieron explicaciones (evaporación, convección, gases disueltos, enlaces de hidrógeno) y en paralelo se cuestionó si el efecto es real o un artefacto experimental. Hoy se estudia como fenómeno general de relajación fuera del equilibrio.",
    q: [
      "El experimento de 2016 que no logró reproducirlo y la respuesta de la comunidad",
      "Versión abstracta: efecto Mpemba en sistemas markovianos",
      "Por qué el sobreenfriamiento complica cualquier medición"
    ]
  },
  {
    t: "Superfluidez",
    c: "Ciencia",
    h: "Un líquido con viscosidad cero que trepa por las paredes del recipiente y se escapa solo.",
    d: "Por debajo de 2,17 K el helio-4 entra en una fase donde fluye sin fricción: pasa por poros infinitesimales, forma películas que ascienden por las paredes (película de Rollin) y vacía el recipiente, y transmite calor mediante ondas en lugar de difusión. Es mecánica cuántica visible a simple vista.",
    q: [
      "Qué es el punto lambda y por qué el helio-3 necesita mil veces menos temperatura",
      "Vórtices cuantizados: por qué solo puede girar en cantidades discretas",
      "Segundo sonido: el calor viajando como una onda"
    ]
  },
  {
    t: "Materiales auxéticos",
    c: "Ciencia",
    h: "Estíralos y en vez de adelgazar, engordan.",
    d: "Casi todo lo que estiras se estrecha (piensa en una goma elástica). Los materiales auxéticos tienen coeficiente de Poisson negativo: su microestructura, con celdas reentrantes, se despliega al tirar y se ensancha en perpendicular. Se usan en protecciones, stents y textiles que absorben impactos mejor que la espuma.",
    q: [
      "Qué es el coeficiente de Poisson y por qué puede ser negativo",
      "Geometrías reentrantes y quirales que producen el efecto",
      "Auxéticos naturales: piel de gato, tendones, ciertas zeolitas"
    ]
  },
  {
    t: "El límite de Landauer",
    c: "Ciencia",
    h: "Borrar un bit de información tiene un coste físico mínimo en calor. La información es termodinámica.",
    d: "Rolf Landauer demostró en 1961 que borrar un bit disipa al menos kT·ln2 julios. Calcular en sí puede ser gratis; destruir información no. De ahí nació la computación reversible y la resolución del demonio de Maxwell: el demonio no viola la segunda ley porque necesita olvidar lo que ha medido.",
    q: [
      "El demonio de Maxwell y cómo lo resolvió Bennett",
      "Experimentos que midieron el límite en el laboratorio (2012 en adelante)",
      "Qué es una puerta lógica reversible (puerta de Toffoli)"
    ]
  },
  {
    t: "Hielo superiónico",
    c: "Ciencia",
    h: "Hielo negro, conductor de electricidad y caliente como el Sol. Probablemente hay océanos de él dentro de Neptuno.",
    d: "A presiones enormes, el agua adopta una fase donde el oxígeno queda fijo en una red cristalina mientras los protones fluyen libremente entre huecos, como un metal líquido dentro de un sólido. Se predijo en 1988 y se confirmó con láseres de choque en 2019. Explicaría los campos magnéticos torcidos de Urano y Neptuno.",
    q: [
      "Cuántas fases del hielo se conocen y cómo se nombran",
      "Cómo se recrea con compresión por láser en nanosegundos",
      "La relación con los campos magnéticos no dipolares de los gigantes helados"
    ]
  },

  // ── Historia ────────────────────────────────────────────────────────────
  {
    t: "El mecanismo de Anticitera",
    c: "Historia",
    h: "Un ordenador analógico de bronce, del siglo II a.C., encontrado en un naufragio.",
    d: "Buscadores de esponjas rescataron en 1901 una masa de bronce corroído. Ochenta años y varias tomografías después se sabe que contenía al menos 30 engranajes que predecían posiciones planetarias, eclipses y el calendario de los Juegos. No se conoce nada de complejidad comparable hasta los relojes astronómicos del siglo XIV.",
    q: [
      "El engranaje diferencial y el movimiento anómalo de la Luna",
      "Quién pudo construirlo: la pista de Rodas y Hiparco",
      "Reconstrucciones modernas y qué partes siguen siendo hipótesis"
    ]
  },
  {
    t: "La República de Cospaia",
    c: "Historia",
    h: "Un error de cartografía creó un país de 330 habitantes sin gobierno, sin impuestos y sin cárcel. Duró 385 años.",
    d: "En 1440 el Papa vendió un territorio a Florencia, pero los dos mapas usaban ríos distintos como frontera y quedó una franja de tierra que nadie reclamó. Los vecinos declararon república: sin ejército, sin leyes escritas, solo un consejo de familias y una inscripción en la iglesia: 'Perpetua et firma libertas'. Vivieron del contrabando de tabaco hasta 1826.",
    q: [
      "Cómo se resolvían los conflictos sin tribunales",
      "El papel del tabaco y del contrabando en su economía",
      "Otros microestados nacidos de errores de tratados"
    ]
  },
  {
    t: "La manía danzante de 1518",
    c: "Historia",
    h: "En Estrasburgo, cientos de personas bailaron durante semanas sin poder parar. Algunas murieron.",
    d: "Empezó con una mujer, Frau Troffea, bailando sola en la calle. En un mes había hasta 400 personas. Las autoridades, convencidas de que era una enfermedad de la sangre, contrataron músicos y habilitaron un mercado para que bailaran más. Es el caso mejor documentado de enfermedad psicógena de masas.",
    q: [
      "Hipótesis del cornezuelo del centeno frente a la explicación psicosocial",
      "Otras epidemias de histeria colectiva documentadas (Tanganica 1962)",
      "El contexto de hambruna y culto a San Vito"
    ]
  },
  {
    t: "Nan Madol",
    c: "Historia",
    h: "Una ciudad de 92 islas artificiales construida sobre un arrecife con columnas de basalto de 50 toneladas.",
    d: "En Pohnpei, Micronesia, la dinastía Saudeleur levantó entre los siglos XII y XVII un complejo de canales e islotes hechos apilando prismas naturales de basalto como troncos. No hay agua potable ni comida en el lugar: todo se traía. Nadie ha explicado con certeza cómo movieron las piedras.",
    q: [
      "Quiénes eran los Saudeleur y cómo cayeron",
      "Técnicas propuestas para transportar el basalto sin poleas",
      "Por qué se la llama 'la Venecia del Pacífico' y su estado de conservación"
    ]
  },
  {
    t: "El colapso de la Edad del Bronce",
    c: "Historia",
    h: "Hacia 1177 a.C. ocho civilizaciones conectadas se derrumbaron casi a la vez. Nadie sabe exactamente por qué.",
    d: "Micénicos, hititas, ugaríticos y buena parte del comercio del Mediterráneo oriental desaparecieron en pocas décadas. Se han propuesto los 'Pueblos del Mar', una megasequía, terremotos en cadena, el colapso de rutas comerciales y la interrupción del suministro de estaño. La hipótesis actual apunta a un fallo sistémico: demasiada interdependencia, poca resiliencia.",
    q: [
      "Quiénes eran los Pueblos del Mar y qué evidencia hay realmente",
      "Las cartas de Ugarit escritas mientras la ciudad caía",
      "Qué dice el registro paleoclimático sobre la sequía de 1200 a.C."
    ]
  },
  {
    t: "Las bibliotecas de Tombuctú",
    c: "Historia",
    h: "Cientos de miles de manuscritos medievales de astronomía y derecho, escondidos en casas del Sahel.",
    d: "Entre los siglos XIII y XVI Tombuctú fue un centro universitario con manuscritos sobre matemáticas, medicina, música y jurisprudencia. Muchos siguen en manos de familias que los heredaron. En 2012, ante la ocupación yihadista, bibliotecarios sacaron clandestinamente unos 350.000 manuscritos en baúles y canoas hasta Bamako.",
    q: [
      "Qué contienen realmente los manuscritos (más allá del Corán)",
      "La operación de rescate de Abdel Kader Haidara",
      "Retos de conservación del papel en clima sahariano"
    ]
  },
  {
    t: "La expedición de Darién",
    c: "Historia",
    h: "Escocia apostó una quinta parte de su dinero a una colonia en Panamá. La perdió y acabó fusionándose con Inglaterra.",
    d: "En 1698 Escocia intentó fundar Caledonia en el istmo de Darién para controlar el comercio entre océanos. Enviaron mercancías inútiles (pelucas, peines), no anticiparon la malaria ni el bloqueo inglés y murieron unos 2.000 colonos. La ruina financiera fue determinante para aceptar el Acta de Unión de 1707.",
    q: [
      "Por qué el clima y las enfermedades eran letales en Darién",
      "Papel de Inglaterra y de la Compañía de las Indias Orientales",
      "Cómo se conecta el desastre con el Acta de Unión"
    ]
  },
  {
    t: "Çatalhöyük",
    c: "Historia",
    h: "Una ciudad de 9.000 años sin calles: se entraba por el techo y se enterraba a los muertos bajo la cama.",
    d: "En Anatolia, hasta 8.000 personas vivieron en casas pegadas unas a otras, sin plazas ni edificios públicos evidentes, sin señales claras de jerarquía. Se circulaba por las azoteas. Los muertos se enterraban bajo el suelo doméstico y las paredes se repintaban decenas de veces con toros, buitres y manos.",
    q: [
      "Qué indica la ausencia de templos o palacios sobre su organización social",
      "Los enterramientos domésticos y la relación con los antepasados",
      "Qué dice el análisis isotópico de sus dietas y su salud"
    ]
  },
  {
    t: "Las torres del silencio",
    c: "Historia",
    h: "Una tradición que considera contaminante enterrar o quemar a los muertos, y los ofrece a los buitres.",
    d: "En el zoroastrismo la tierra, el fuego y el agua son puros y un cadáver los profanaría. La solución fue la dakhma: una torre circular donde los cuerpos se exponen al sol y a las aves carroñeras. La práctica está en crisis en Bombay desde que el diclofenaco veterinario diezmó a los buitres de la India.",
    q: [
      "Cosmología zoroástrica: por qué el cadáver es impuro",
      "El colapso de las poblaciones de buitre por diclofenaco",
      "Alternativas modernas (concentradores solares) y debate en la comunidad parsi"
    ]
  },

  // ── Mente ───────────────────────────────────────────────────────────────
  {
    t: "Afantasía",
    c: "Mente",
    h: "Cierra los ojos e imagina una manzana. Entre un 1 y un 4 % de la gente no ve absolutamente nada.",
    d: "La afantasía es la ausencia de imaginería mental voluntaria. Mucha gente la descubre de adulta, al darse cuenta de que 'contar ovejas' no era una metáfora para los demás. No implica peor memoria ni menos creatividad: se recuerda de forma conceptual en lugar de visual. En el extremo opuesto está la hiperfantasía.",
    q: [
      "El cuestionario VVIQ y cómo se mide algo puramente subjetivo",
      "Afantasía y memoria autobiográfica: qué se pierde y qué no",
      "Qué pasa con los sueños en personas afantásicas"
    ]
  },
  {
    t: "El efecto de la lengua extranjera",
    c: "Mente",
    h: "Piensas un dilema moral en tu segundo idioma y tomas decisiones distintas.",
    d: "En experimentos con el dilema del tranvía, la gente es notablemente más utilitarista cuando responde en un idioma que aprendió después. El idioma extranjero reduce la carga emocional y la aversión a las pérdidas, y activa un razonamiento más deliberado. Tiene implicaciones para negociaciones, juicios e instituciones multilingües.",
    q: [
      "Estudios de Keysar y Costa sobre decisión moral bilingüe",
      "Cómo interactúa con la aversión al riesgo y la contabilidad mental",
      "Qué implica para peritajes y declaraciones judiciales con intérprete"
    ]
  },
  {
    t: "La paradoja de Moravec",
    c: "Mente",
    h: "Para una máquina es fácil jugar al ajedrez y dificilísimo subir una escalera.",
    d: "Hans Moravec observó en los 80 que el razonamiento abstracto, que a los humanos nos cuesta, requiere poquísimo cómputo, mientras que percibir y moverse, que hacemos sin pensar, requiere muchísimo. La explicación evolutiva: la percepción sensoriomotora lleva optimizándose cientos de millones de años; el álgebra, unos miles.",
    q: [
      "Cómo se ve la paradoja hoy en robótica frente a los modelos de lenguaje",
      "El problema de la manipulación fina y por qué sigue sin resolverse",
      "Relación con el conocimiento tácito de Polanyi"
    ]
  },
  {
    t: "El cerebro predictivo",
    c: "Mente",
    h: "No ves el mundo: ves la predicción que tu cerebro hace del mundo, corregida por los errores.",
    d: "La codificación predictiva propone que el cerebro genera constantemente un modelo de lo que espera percibir y solo transmite hacia arriba la diferencia con lo que llega de los sentidos. Explica ilusiones, el efecto placebo y por qué el tiempo parece pasar más rápido en entornos familiares. Karl Friston la generalizó con el principio de energía libre.",
    q: [
      "Qué es el error de predicción y cómo se propaga en la corteza",
      "Alucinaciones y psicosis como fallo de precisión de las predicciones",
      "El principio de energía libre explicado sin matemáticas"
    ]
  },
  {
    t: "Ideastesia",
    c: "Mente",
    h: "No es que la letra A sea roja: es que el concepto de A evoca el rojo.",
    d: "Danko Nikolić propuso reinterpretar la sinestesia: lo que dispara la experiencia no es el estímulo sensorial sino el significado. Si te muestran un símbolo ambiguo, el color que 'ves' cambia según lo leas como una S o como un 5. Sugiere que percepción y conceptualización están mucho más entrelazadas de lo que asumimos.",
    q: [
      "Experimentos con símbolos ambiguos y cambio de color percibido",
      "Diferencia entre sinestesia clásica e ideastesia",
      "Sinestesia y aprendizaje: ¿se puede entrenar?"
    ]
  },
  {
    t: "El síndrome de la mano ajena",
    c: "Mente",
    h: "Una mano que actúa por su cuenta: desabrocha lo que la otra abrocha, y su dueño la siente extraña.",
    d: "Tras ciertas lesiones del cuerpo calloso o del área motora suplementaria, una mano ejecuta acciones complejas e intencionadas que la persona no reconoce como propias. Es una ventana brutal a cómo el sentido de agencia (sentir que yo lo hice) es un mecanismo cerebral separado del movimiento mismo.",
    q: [
      "Pacientes con cerebro escindido y los experimentos de Sperry y Gazzaniga",
      "Cómo se construye el sentido de agencia y cómo se puede engañar",
      "El intérprete del hemisferio izquierdo inventando explicaciones"
    ]
  },
  {
    t: "Memoria autobiográfica superior",
    c: "Mente",
    h: "Personas capaces de decirte qué comieron y qué tiempo hizo un martes cualquiera de hace 20 años.",
    d: "La hipertimesia (HSAM) afecta a unas pocas decenas de casos documentados. No es memoria fotográfica: fallan en tests de memoria normales igual que cualquiera, pero su recuerdo autobiográfico es casi exhaustivo. Muchos describen la imposibilidad de olvidar como una carga, no como un don.",
    q: [
      "Diferencias anatómicas encontradas en el lóbulo temporal y el núcleo caudado",
      "Por qué olvidar es funcionalmente necesario",
      "El caso de Solomon Shereshevsky descrito por Luria"
    ]
  },

  // ── Lenguaje ────────────────────────────────────────────────────────────
  {
    t: "El silbo gomero",
    c: "Lenguaje",
    h: "Una isla entera que conversa a tres kilómetros de distancia, silbando el idioma.",
    d: "En La Gomera, el español se transpone a un sistema de silbidos con dos vocales y cuatro consonantes distinguibles, capaz de transmitir cualquier frase por barrancos donde gritar es inútil. Casi desapareció con el teléfono; hoy es asignatura obligatoria en la escuela y Patrimonio de la Humanidad.",
    q: [
      "Cómo se codifican las vocales y consonantes en tono y quiebros",
      "Otras lenguas silbadas: Kuşköy en Turquía, mazateco en México",
      "Qué zonas del cerebro procesan el silbo en hablantes expertos"
    ]
  },
  {
    t: "Guugu Yimithirr",
    c: "Lenguaje",
    h: "Un idioma sin 'izquierda' ni 'derecha': todo se dice en norte, sur, este y oeste, hasta dónde tienes la mosca.",
    d: "En esta lengua del norte de Australia el espacio es siempre absoluto: 'tienes una hormiga en la pierna sur'. Sus hablantes mantienen una brújula mental permanente, incluso dentro de edificios o tras viajar en avión. Es el caso más citado del debate sobre si la lengua moldea la cognición.",
    q: [
      "Los trabajos de Levinson y el experimento de la mesa rotada",
      "Marcos de referencia relativo, absoluto e intrínseco",
      "Qué queda en pie hoy de la hipótesis de Sapir-Whorf"
    ]
  },
  {
    t: "El pirahã y los números",
    c: "Lenguaje",
    h: "Una lengua amazónica sin numerales, sin nombres de colores fijos y aparentemente sin subordinación.",
    d: "Daniel Everett describió que el pirahã carece de palabras para cantidades exactas y de recursión gramatical, lo que desafiaría la gramática universal de Chomsky. La polémica lingüística fue feroz. En paralelo, los experimentos mostraron que sin numerales es muy difícil igualar conjuntos de más de tres objetos.",
    q: [
      "El debate Everett-Chomsky sobre la recursión",
      "Experimentos de correspondencia de cantidades sin numerales",
      "El principio de inmediatez de la experiencia que propuso Everett"
    ]
  },
  {
    t: "El idioma de señas de Nicaragua",
    c: "Lenguaje",
    h: "En los años 80, un grupo de niños sordos inventó desde cero una lengua completa. Los lingüistas lo vieron ocurrir.",
    d: "Al abrirse las primeras escuelas para sordos en Managua, los alumnos llegaron con gestos caseros incompatibles. En pocos años crearon un pidgin y la siguiente generación de niños, más pequeña, lo convirtió en una lengua con gramática, concordancia espacial y morfología. Es la observación más directa del nacimiento de un idioma.",
    q: [
      "Diferencia entre las cohortes de hablantes y cómo se complejizó la gramática",
      "Qué es la criollización y por qué la impulsan los niños",
      "Qué implica sobre el periodo crítico de adquisición del lenguaje"
    ]
  },
  {
    t: "Rongorongo",
    c: "Lenguaje",
    h: "Las tablillas de Rapa Nui: una escritura que se lee girando la tablilla 180° cada renglón. Y sigue sin descifrarse.",
    d: "Se conservan un par de docenas de piezas con glifos tallados en bustrofedón inverso. Los últimos que sabían leerlas murieron por las epidemias y las redadas esclavistas del siglo XIX. No se sabe si es escritura plena, proto-escritura o un sistema mnemotécnico ritual.",
    q: [
      "Qué es el bustrofedón inverso y cómo se dedujo la dirección de lectura",
      "El calendario lunar identificado en la tablilla Mamari",
      "Por qué el corpus es demasiado pequeño para un desciframiento estadístico"
    ]
  },
  {
    t: "Los quipus incas",
    c: "Lenguaje",
    h: "Un imperio administrado con nudos de colores. Algunos podrían codificar algo más que números.",
    d: "El quipu registra cantidades en base diez mediante tipos de nudo y posición, y los quipucamayocs llevaban así censos, tributos y calendarios. Pero hay quipus 'narrativos' cuyos patrones no encajan con lo numérico, y se investiga si codificaban nombres, lugares o relatos.",
    q: [
      "Cómo se leen los nudos: posición, tipo y color",
      "El proyecto Khipu de Harvard y los hallazgos de Santa (2005)",
      "Quipus patrimoniales todavía custodiados en pueblos andinos"
    ]
  },
  {
    t: "Toki pona",
    c: "Lenguaje",
    h: "Un idioma completo con 137 palabras, diseñado para ver qué pasa cuando piensas con lo mínimo.",
    d: "Sonja Lang lo creó en 2001 como experimento filosófico y terapéutico: sin palabras específicas, todo se describe combinando conceptos básicos ('coche' es 'cosa que se mueve'). Obliga a decidir qué es esencial en lo que quieres decir. Tiene una comunidad activa y libros traducidos.",
    q: [
      "Cómo se expresan conceptos técnicos con vocabulario mínimo",
      "Otras lenguas construidas con fines cognitivos: lojban, ithkuil",
      "Qué revela la ambigüedad forzada sobre el contexto en la comunicación"
    ]
  },
  {
    t: "El manuscrito Voynich",
    c: "Lenguaje",
    h: "240 páginas del siglo XV, con plantas que no existen, escritas en un sistema que nadie ha roto.",
    d: "El pergamino está datado por carbono 14 entre 1404 y 1438. El texto muestra estadísticas propias de un lenguaje real (ley de Zipf, entropía baja) pero no coincide con ningún idioma conocido. Cada década aparece una 'solución' que la comunidad acaba descartando.",
    q: [
      "Qué dicen los análisis estadísticos sobre si es un texto con sentido",
      "Principales hipótesis: cifrado, lengua construida, glosolalia, fraude",
      "Por qué las secciones botánica, astronómica y balnearia parecen distintas"
    ]
  },

  // ── Naturaleza ──────────────────────────────────────────────────────────
  {
    t: "La medusa inmortal",
    c: "Naturaleza",
    h: "Ante el estrés, rebobina su ciclo vital y vuelve a ser una cría. Puede repetirlo indefinidamente.",
    d: "Turritopsis dohrnii puede revertir de medusa adulta a pólipo mediante transdiferenciación: sus células cambian de tipo, algo que casi ningún animal hace. En el mar muere igualmente comida o infectada, pero biológicamente no tiene senescencia obligatoria. Su genoma se secuenció en 2022 buscando pistas sobre el envejecimiento.",
    q: [
      "Qué es la transdiferenciación celular y qué la hace tan rara",
      "Qué encontró la comparación genómica de 2022 sobre reparación del ADN",
      "Otros animales con senescencia despreciable: hidra, rata topo desnuda"
    ]
  },
  {
    t: "Physarum polycephalum",
    c: "Naturaleza",
    h: "Un organismo sin neuronas que resuelve laberintos y reconstruyó la red de metro de Tokio.",
    d: "Este moho mucilaginoso es una única célula gigante con muchos núcleos. Explora el entorno extendiendo tubos y refuerza los que llevan a comida mientras retrae el resto. En un experimento de 2010, colocando avena en las ciudades del área de Tokio, reprodujo una red casi idéntica a la ferroviaria real en eficiencia.",
    q: [
      "Cómo optimiza rutas sin sistema nervioso (refuerzo y poda de tubos)",
      "El experimento de la red de Tokio de Tero y Nakagaki",
      "Memoria externa: cómo evita zonas ya exploradas mediante rastros"
    ]
  },
  {
    t: "Ophiocordyceps",
    c: "Naturaleza",
    h: "Un hongo que secuestra el comportamiento de una hormiga y la obliga a morir en el sitio óptimo para esporular.",
    d: "El hongo infecta a hormigas carpinteras y, sin invadir el cerebro, coordina químicamente sus músculos para que trepen a una altura concreta, muerdan una hoja con una fuerza que les disloca la mandíbula y queden fijas. Días después el estroma emerge de su cabeza. La orientación y la altura de la 'mordedura de la muerte' son sorprendentemente consistentes.",
    q: [
      "Cómo controla los músculos sin entrar en el cerebro (hallazgo de 2017)",
      "La respuesta de las colonias: higiene social y retirada de infectados",
      "Registro fósil: hojas de hace 48 millones de años con marcas de mordedura"
    ]
  },
  {
    t: "Pando",
    c: "Naturaleza",
    h: "40.000 troncos de álamo que en realidad son un único organismo de 6.000 toneladas y miles de años.",
    d: "En Utah, un bosque entero es un solo individuo clonal conectado por un sistema radicular común, con un ADN idéntico en todos sus tallos. Es uno de los organismos más pesados que se conocen. Está en declive: los ciervos se comen los brotes jóvenes y casi no hay regeneración desde hace décadas.",
    q: [
      "Cómo se determinó que es un único clon y no un bosque normal",
      "Por qué el exceso de herbívoros impide la regeneración",
      "Otros organismos clonales gigantes: Posidonia oceanica, Armillaria"
    ]
  },
  {
    t: "La magnetorrecepción de las aves",
    c: "Naturaleza",
    h: "Puede que los petirrojos vean el campo magnético terrestre como un patrón superpuesto sobre lo que miran.",
    d: "La hipótesis más sólida implica al criptocromo de la retina: la luz azul crea un par de radicales cuyo espín se ve alterado por el campo magnético, cambiando la señal química. Sería un efecto cuántico funcionando a temperatura ambiente en un ser vivo. Se estudia también la magnetita en el pico.",
    q: [
      "Mecanismo del par de radicales y por qué necesita luz azul",
      "Experimentos con campos oscilantes que desorientan a las aves",
      "Estado del campo de la biología cuántica: qué está probado y qué no"
    ]
  },
  {
    t: "El camarón mantis",
    c: "Naturaleza",
    h: "Doce a dieciséis tipos de fotorreceptor, visión de luz polarizada y un golpe que hierve el agua.",
    d: "Sus ojos, montados en tallos móviles, detectan luz polarizada circularmente, algo único en la naturaleza. Curiosamente, distinguen colores peor que nosotros: parece que no comparan canales, sino que reconocen firmas espectrales directamente. Su golpe acelera como una bala del calibre 22 y produce cavitación luminosa.",
    q: [
      "Por qué más fotorreceptores no significa mejor discriminación de color",
      "Luz polarizada circular: para qué la usarían (comunicación privada)",
      "Cavitación: cómo la burbuja del golpe emite luz y calor"
    ]
  },
  {
    t: "El quórum de las abejas",
    c: "Naturaleza",
    h: "Un enjambre elige su nueva casa votando, y sabe cuándo dejar de deliberar.",
    d: "Las exploradoras inspeccionan cavidades y bailan con una intensidad proporcional a la calidad del sitio. Otras van a verificarlo por sí mismas. Cuando en un candidato se acumula un número umbral de exploradoras, emiten señales de tope que silencian a las rivales y el enjambre despega. Es un algoritmo distribuido sin líder.",
    q: [
      "Las señales de 'stop' y cómo cortan el debate",
      "Trabajo de Thomas Seeley y sus experimentos en islas",
      "Paralelismos entre el quórum de la colmena y la decisión neuronal"
    ]
  },
  {
    t: "Prototaxites",
    c: "Naturaleza",
    h: "Antes de que existieran los árboles, lo más alto del paisaje eran hongos de ocho metros.",
    d: "Durante el Silúrico y el Devónico, cuando las plantas terrestres apenas llegaban a la rodilla, existían estructuras de hasta 8 metros de alto y un metro de ancho. Se debatió durante un siglo si eran algas, coníferas o líquenes; los isótopos apuntan a un organismo fúngico, aunque su clasificación exacta sigue abierta.",
    q: [
      "Por qué el análisis isotópico sugirió que era heterótrofo",
      "Cómo era el paisaje terrestre del Devónico temprano",
      "El estudio reciente que propone que no encaja en ningún reino actual"
    ]
  },
  {
    t: "Redes micorrízicas",
    c: "Naturaleza",
    h: "Hongos que conectan las raíces de un bosque e intercambian carbono entre árboles distintos.",
    d: "Los hongos micorrízicos envuelven las raíces y transportan nutrientes a cambio de azúcares. Suzanne Simard mostró con isótopos que el carbono viaja entre árboles conectados, lo que popularizó la idea del 'wood wide web'. Desde 2023 hay una fuerte revisión crítica: la evidencia de cooperación deliberada entre árboles es más débil de lo que se contó.",
    q: [
      "Qué demostraron realmente los experimentos con carbono marcado",
      "La crítica de Karst, Jones y Hoeksema a la narrativa del 'wood wide web'",
      "Diferencia entre micorriza arbuscular y ectomicorriza"
    ]
  },

  // ── Cosmos ──────────────────────────────────────────────────────────────
  {
    t: "La estrella de Tabby",
    c: "Cosmos",
    h: "Una estrella cuyo brillo cae hasta un 22 % de forma irregular. Se llegó a proponer una megaestructura alienígena.",
    d: "KIC 8462851 mostró en los datos de Kepler caídas de luz que ningún planeta podría causar. Tras descartar cometas y agujeros, se propuso en serio una esfera de Dyson parcial. Las campañas posteriores mostraron que el oscurecimiento depende del color, lo que apunta a polvo fino, aunque el origen exacto sigue sin cerrarse.",
    q: [
      "Por qué la dependencia del color descarta un objeto sólido",
      "Qué es una esfera de Dyson y cómo se buscaría de verdad",
      "Otras estrellas con curvas de luz anómalas descubiertas después"
    ]
  },
  {
    t: "Objetos de Thorne-Żytkow",
    c: "Cosmos",
    h: "Una estrella gigante con una estrella de neutrones latiendo en su interior.",
    d: "Si en un sistema binario una supergigante roja engulle a su compañera de neutrones, el resultado sería una estrella híbrida cuyo núcleo no es fusión normal sino materia degenerada. Se predijeron en 1977 y producirían una firma química rara (rubidio, molibdeno). Hay un par de candidatos, ninguno confirmado.",
    q: [
      "Qué es el proceso irp y la firma química que dejaría",
      "Estado actual del candidato HV 2112",
      "Cómo se formaría el sistema binario necesario"
    ]
  },
  {
    t: "El Gran Atractor",
    c: "Cosmos",
    h: "Algo está arrastrando a nuestra galaxia a 600 km/s y está oculto justo detrás del disco de la Vía Láctea.",
    d: "El Grupo Local se mueve respecto al fondo cósmico de microondas hacia una región en la 'zona de evitación', tapada por el polvo de nuestra propia galaxia. Se identificó una concentración de masa en Norma, aunque hoy se cree que buena parte del tirón viene de más lejos, del supercúmulo de Shapley. Laniakea es el mapa de ese flujo.",
    q: [
      "Qué es la zona de evitación y cómo se observa a través de ella",
      "Laniakea: cómo se define un supercúmulo por flujos de velocidad",
      "El papel del Repelente del Dipolo descubierto en 2017"
    ]
  },
  {
    t: "Planetas errantes",
    c: "Cosmos",
    h: "Mundos sin sol, vagando en la oscuridad interestelar. Podrían ser más numerosos que las estrellas.",
    d: "Expulsados de sus sistemas o formados en solitario, se detectan por microlente gravitacional: el instante en que su gravedad amplifica la luz de una estrella detrás. Algunos podrían mantener océanos bajo el hielo gracias al calor interno. El JWST encontró además parejas de objetos de masa joviana flotando juntos en Orión.",
    q: [
      "Cómo funciona la microlente gravitacional para detectarlos",
      "¿Podría haber vida bajo el hielo en un planeta sin estrella?",
      "Los objetos JuMBO de Orión y por qué desconciertan"
    ]
  },
  {
    t: "La lente gravitacional solar",
    c: "Cosmos",
    h: "A 550 unidades astronómicas del Sol hay un punto donde nuestra estrella funciona como telescopio gigante.",
    d: "La gravedad del Sol curva la luz y la enfoca a partir de unas 550 UA. Una sonda situada allí podría obtener imágenes de exoplanetas con resolución de kilómetros, algo inalcanzable para cualquier telescopio construible. El reto es llegar: son más de diez veces la distancia de Plutón y hay que apuntar con precisión extrema.",
    q: [
      "Cómo se calcula la distancia focal y la corona como fuente de ruido",
      "Propuestas de misión de la NASA y velas solares",
      "Cómo se reconstruiría la imagen a partir del anillo de Einstein"
    ]
  },
  {
    t: "Kamoʻoalewa",
    c: "Cosmos",
    h: "La Tierra tiene un cuasi-satélite que probablemente es un trozo de la Luna arrancado por un impacto.",
    d: "Este asteroide de unos 50 metros acompaña a la Tierra en una órbita en herradura desde hace un siglo y lo seguirá haciendo unos siglos más. Su espectro coincide con muestras lunares, lo que sugiere que salió despedido de un cráter. China lanzó la misión Tianwen-2 para traer muestras.",
    q: [
      "Qué es una órbita en herradura y en qué se diferencia de una luna",
      "La evidencia espectral del origen lunar",
      "Objetivos y calendario de la misión Tianwen-2"
    ]
  },

  // ── Tecnología ──────────────────────────────────────────────────────────
  {
    t: "Reflections on Trusting Trust",
    c: "Tecnología",
    h: "Ken Thompson demostró que puedes esconder una puerta trasera que no aparece en ningún código fuente.",
    d: "En su discurso del Turing de 1984 mostró cómo modificar un compilador para que inserte una puerta trasera al compilar el programa de login, y además se reinserte a sí mismo al compilar el propio compilador. Luego borras el código malicioso: el binario perpetúa el ataque para siempre. La conclusión: no puedes confiar en código que no has escrito tú, ni siquiera en tu compilador.",
    q: [
      "Cómo funciona el quine que se reinyecta al recompilar",
      "Compilación diversa doble (DDC) de David A. Wheeler como defensa",
      "Builds reproducibles y por qué importan hoy en la cadena de suministro"
    ]
  },
  {
    t: "La Regla 110",
    c: "Tecnología",
    h: "Una regla de cuatro líneas que pinta píxeles blancos y negros es Turing-completa.",
    d: "Los autómatas celulares elementales aplican una regla local a una fila de celdas. La Regla 110 produce estructuras que se desplazan, chocan e interaccionan, y Matthew Cook demostró que puede simular cualquier computación. Es uno de los sistemas más simples conocidos con potencia computacional universal.",
    q: [
      "Qué significa Turing-completo y cómo se demuestra en un autómata",
      "Las clases de complejidad de Wolfram y la 'frontera del caos'",
      "El conflicto legal entre Cook y Wolfram Research"
    ]
  },
  {
    t: "Compartición de secretos de Shamir",
    c: "Tecnología",
    h: "Parte una clave en cinco trozos de forma que tres cualesquiera la reconstruyan y dos no revelen nada.",
    d: "Se basa en que por k puntos pasa exactamente un polinomio de grado k-1. El secreto es el término independiente y cada participante recibe un punto de la curva. Con menos partes de las necesarias, todos los secretos siguen siendo igual de probables: es seguridad perfecta, no computacional. Se usa en custodia de claves raíz y criptomonedas.",
    q: [
      "Por qué k-1 puntos no filtran información alguna (seguridad informacional)",
      "Esquemas de umbral en la práctica: ceremonias de claves raíz de DNSSEC",
      "Diferencia con la firma multiparte (MPC) y multisig"
    ]
  },
  {
    t: "Relojes que miden la gravedad",
    c: "Tecnología",
    h: "Sube un reloj atómico un centímetro y ya marca distinto. Se puede medir.",
    d: "Los relojes ópticos de red tienen tal precisión que detectan la dilatación temporal gravitacional a diferencias de altura milimétricas. Eso los convierte en altímetros: la geodesia cronométrica propone medir la forma del geoide comparando relojes. También sirven para buscar variaciones de las constantes fundamentales y materia oscura.",
    q: [
      "Qué es un reloj de red óptica y por qué supera al cesio",
      "Geodesia cronométrica: medir alturas con relojes",
      "Cómo se buscaría materia oscura ultraligera con relojes"
    ]
  },
  {
    t: "El proyecto Xanadu",
    c: "Tecnología",
    h: "El hipertexto que se diseñó antes que la web, con enlaces de doble sentido y sin páginas rotas.",
    d: "Ted Nelson acuñó 'hipertexto' en 1965 y propuso documentos con transclusión (citar mostrando el original vivo), enlaces bidireccionales, versionado y micropagos automáticos al autor. Es el proyecto de software más largo de la historia: 54 años hasta una versión pública. La web ganó por ser simple y tolerar enlaces rotos.",
    q: [
      "Qué es la transclusión y por qué resolvería el problema de la cita",
      "Enlaces bidireccionales: cómo lo intentan hoy Roam, Obsidian o el fediverso",
      "La crítica de Nelson a la web y qué parte tenía razón"
    ]
  },
  {
    t: "Códigos Reed-Solomon",
    c: "Tecnología",
    h: "Por qué un CD rayado sigue sonando y una sonda a mil millones de kilómetros se entiende sin errores.",
    d: "Codifican los datos como puntos de un polinomio y añaden puntos extra: si se pierden o corrompen algunos, el polinomio original se reconstruye igual. Están en los CD, los códigos QR, los discos RAID y las comunicaciones de las Voyager. Es una idea de 1960 que sigue siendo infraestructura invisible.",
    q: [
      "Intuición polinómica: por qué la redundancia permite corregir, no solo detectar",
      "Cómo un código QR sobrevive a que le tapes un 30 %",
      "Códigos concatenados y turbo códigos en el espacio profundo"
    ]
  },
  {
    t: "El MONIAC",
    c: "Tecnología",
    h: "Un ordenador hecho de agua coloreada y tuberías que simulaba la economía de un país.",
    d: "Bill Phillips construyó en 1949 una máquina hidráulica donde el agua representaba el flujo de dinero: depósitos para ahorro, impuestos e inversión, válvulas para tipos de interés. Modelaba ecuaciones keynesianas de forma analógica y visible, y se usó para enseñar en la LSE. Quedan unas pocas unidades funcionando.",
    q: [
      "Qué ecuaciones macroeconómicas implementaba físicamente",
      "Computación analógica: ventajas frente a la digital y por qué desapareció",
      "La curva de Phillips y quién fue su autor"
    ]
  },
  {
    t: "La constante de Chaitin",
    c: "Tecnología",
    h: "Un número real, perfectamente definido, cuyos dígitos son imposibles de calcular casi todos.",
    d: "Omega es la probabilidad de que un programa aleatorio termine de ejecutarse. Está bien definido, pero conocer sus primeros bits resolvería el problema de la parada para programas cortos y, con ello, un montón de conjeturas matemáticas abiertas. Es aleatoriedad demostrable dentro de las matemáticas puras.",
    q: [
      "Relación entre Omega y el problema de la parada",
      "Qué es la aleatoriedad algorítmica (Kolmogorov-Chaitin)",
      "Cómo se calcularon los primeros bits para una máquina concreta"
    ]
  },

  // ── Sociedad ────────────────────────────────────────────────────────────
  {
    t: "La hawala",
    c: "Sociedad",
    h: "Un sistema para mover dinero entre continentes sin que se mueva ningún dinero.",
    d: "Funciona desde el siglo VIII: entregas efectivo a un intermediario, que llama a un colega en el país de destino y este paga al receptor con una contraseña. No hay transferencia, solo deudas entre agentes que se compensan después. Es rápido, barato y opaco, lo que lo hace vital para migrantes y problemático para los reguladores.",
    q: [
      "Cómo se liquidan las deudas entre agentes (netting y contra-hawala)",
      "Por qué sobrevive frente a la banca formal en corredores de remesas",
      "El debate regulatorio tras 2001 y el coste para los migrantes"
    ]
  },
  {
    t: "Las piedras rai de Yap",
    c: "Sociedad",
    h: "Dinero de piedra de cuatro toneladas que no se mueve. Una de las más valiosas está en el fondo del mar.",
    d: "En Yap se usaban discos de calcita traídos en canoa desde otra isla. Como eran intransportables, cambiaba solo la propiedad, reconocida por consenso oral de la comunidad: un registro distribuido sin registro escrito. Se cuenta que una piedra se hundió en el trayecto y siguió considerándose válida. Los economistas la citan para explicar qué es realmente el dinero.",
    q: [
      "El artículo de Milton Friedman sobre Yap y el patrón oro",
      "Por qué se cita como precedente conceptual de blockchain",
      "Qué pasó con el valor cuando un comerciante trajo piedras en barco"
    ]
  },
  {
    t: "El efecto cobra",
    c: "Sociedad",
    h: "Pagas por cada cobra muerta y acabas con más cobras que antes.",
    d: "La anécdota colonial india cuenta que el incentivo generó criaderos de cobras; al cancelarlo, los criadores las soltaron. Es el ejemplo clásico de la ley de Goodhart: cuando una medida se convierte en objetivo, deja de ser buena medida. Ocurre con listas de espera, métricas escolares, KPI comerciales y modelos de IA.",
    q: [
      "Ley de Goodhart y ley de Campbell: enunciados y diferencias",
      "Casos reales documentados de incentivos perversos en políticas públicas",
      "Especificación de objetivos en IA (reward hacking)"
    ]
  },
  {
    t: "Elinor Ostrom y los comunes",
    c: "Sociedad",
    h: "La 'tragedia de los comunes' se dio por inevitable durante 40 años. Ella fue a mirar sobre el terreno y no lo era.",
    d: "Frente al dilema de que todo recurso compartido acaba esquilmado, Ostrom documentó comunidades (regantes de Valencia, pastos suizos, pesquerías) que gestionan bienes comunes de forma sostenible durante siglos. Destiló ocho principios de diseño institucional. Fue la primera mujer en recibir el Nobel de Economía, en 2009.",
    q: [
      "Los ocho principios de diseño de instituciones duraderas",
      "El Tribunal de las Aguas de Valencia como caso de estudio",
      "Límites: cuándo sí falla la gestión comunal"
    ]
  },
  {
    t: "El experimento Mincome",
    c: "Sociedad",
    h: "Un pueblo canadiense probó la renta básica en los 70. Los datos se guardaron en cajas y nadie los miró en 30 años.",
    d: "Entre 1974 y 1979, en Dauphin (Manitoba), todos los vecinos pudieron acceder a un ingreso garantizado. El cambio de gobierno canceló el análisis y 1.800 cajas de datos quedaron archivadas. Evelyn Forget los recuperó en 2009: las hospitalizaciones bajaron un 8,5 % y la participación laboral apenas cayó, salvo en madres jóvenes y adolescentes que siguieron estudiando.",
    q: [
      "Qué mide realmente un impuesto negativo sobre la renta",
      "Los hallazgos de Forget en salud y escolarización",
      "Comparación con los ensayos de Finlandia y Kenia (GiveDirectly)"
    ]
  },

  // ── Arte ────────────────────────────────────────────────────────────────
  {
    t: "Conlon Nancarrow",
    c: "Arte",
    h: "Compuso durante 40 años en aislamiento música imposible de tocar, perforando rollos de pianola a mano.",
    d: "Exiliado en México tras luchar en las Brigadas Internacionales, renunció a los intérpretes humanos y escribió directamente sobre rollos de papel. Sus estudios superponen tempos en proporciones irracionales, con cánones donde una voz acelera mientras otra frena. Fue redescubierto en los 80 y Ligeti lo llamó el mayor compositor vivo.",
    q: [
      "Qué es un canon de tempo y cómo suena una relación √2:1",
      "Por qué la pianola le permitía lo que ningún pianista podía",
      "Su influencia en Ligeti y en la música algorítmica posterior"
    ]
  },
  {
    t: "El azul YInMn",
    c: "Arte",
    h: "El primer azul inorgánico nuevo en 200 años apareció por accidente en un horno de laboratorio en 2009.",
    d: "Un equipo de Oregon calentaba óxidos buscando propiedades electrónicas y sacó del horno un polvo azul intensísimo. Su estructura mantiene el manganeso en una coordinación bipiramidal que absorbe rojo y verde. Es más estable y menos tóxico que el azul cobalto, y refleja infrarrojo, así que enfría los edificios que pinta.",
    q: [
      "Por qué era tan difícil encontrar un pigmento azul estable",
      "Historia de los azules: lapislázuli, egipcio, Prusia, cobalto",
      "Pigmentos que reflejan infrarrojo y arquitectura pasiva"
    ]
  },
  {
    t: "El canto difónico",
    c: "Arte",
    h: "Una sola garganta produciendo dos notas a la vez: un bordón grave y una melodía silbada encima.",
    d: "En Tuvá y Mongolia, los cantantes moldean la cavidad bucal para amplificar armónicos concretos de su propio timbre hasta que se oyen como una segunda voz. Existen varios estilos (khoomei, sygyt, kargyraa) y en kargyraa las cuerdas vestibulares vibran a mitad de frecuencia. Se aprende, no es un don.",
    q: [
      "Qué es la serie armónica y cómo se filtra con la boca",
      "Diferencias entre sygyt, khoomei y kargyraa",
      "Análisis espectral de una grabación: cómo verlo en un espectrograma"
    ]
  },
  {
    t: "La tipografía Doves",
    c: "Arte",
    h: "Su creador tiró los tipos de plomo al Támesis para que nadie más los usara. Un siglo después, un diseñador los rescató.",
    d: "Tras romper con su socio, T. J. Cobden-Sanderson arrojó toda la fundición desde el puente de Hammersmith entre 1916 y 1917, en más de cien viajes nocturnos. En 2013 Robert Green reconstruyó digitalmente la letra a partir de impresos y luego, con buzos, se recuperaron 150 piezas del lodo del río.",
    q: [
      "La disputa entre Cobden-Sanderson y Emery Walker",
      "Cómo se digitaliza una tipografía a partir de libros impresos",
      "El movimiento Arts and Crafts y las prensas privadas"
    ]
  },
  {
    t: "El teatro de la memoria",
    c: "Arte",
    h: "Un anfiteatro de madera del siglo XVI diseñado para contener, físicamente, todo el conocimiento humano.",
    d: "Giulio Camillo construyó una estructura donde el espectador se colocaba en el escenario y veía gradas llenas de imágenes simbólicas ordenadas por planetas y niveles. Cada imagen era una llave mnemotécnica hacia un discurso. Es el ancestro conceptual de los palacios de la memoria, de la enciclopedia y de las interfaces espaciales de información.",
    q: [
      "El método de loci y cómo funciona la memoria espacial",
      "El libro El arte de la memoria de Frances Yates",
      "Ecos modernos: memory palaces, hipertexto espacial, zettelkasten"
    ]
  },
  {
    t: "Las cuevas de Sulawesi",
    c: "Arte",
    h: "La escena narrativa más antigua conocida tiene 51.000 años y está en Indonesia, no en Europa.",
    d: "Las dataciones por series de uranio de figuras pintadas en cuevas indonesias desplazaron el foco del arte rupestre fuera del sur de Europa. Una escena muestra figuras teriantrópicas cazando cerdos verrugosos: no es solo un animal, es un relato. Obliga a repensar dónde y cuándo apareció el pensamiento simbólico.",
    q: [
      "Cómo funciona la datación por series de uranio en costras de calcita",
      "Qué es una figura teriantrópica y qué implica cognitivamente",
      "El debate sobre el arte neandertal en Cueva de Ardales y Maltravieso"
    ]
  },

  // ── Lugares ─────────────────────────────────────────────────────────────
  {
    t: "El lago Kivu",
    c: "Lugares",
    h: "Un lago con tanto gas disuelto que podría explotar. Y mientras tanto se usa como central eléctrica.",
    d: "Entre Ruanda y la RDC hay un lago con 300 km³ de CO₂ y 60 km³ de metano atrapados en sus capas profundas por la presión. Un terremoto o una erupción podrían desencadenar una erupción límnica, como la que mató a 1.700 personas en el lago Nyos en 1986. Hoy se extrae el metano para generar electricidad, lo que además reduce el riesgo.",
    q: [
      "Qué fue el desastre del lago Nyos y cómo se desgasifica ahora",
      "Estratificación meromíctica: por qué el gas no sube",
      "Cómo funciona la planta KivuWatt y los riesgos de extraer mal"
    ]
  },
  {
    t: "Socotra",
    c: "Lugares",
    h: "Una isla donde un tercio de las plantas no existe en ningún otro sitio del planeta.",
    d: "Separada de Arabia hace millones de años, Socotra desarrolló una flora propia: el árbol de sangre de dragón con forma de paraguas invertido, el pepino-árbol, decenas de endemismos. Es un laboratorio de evolución insular comparable a Galápagos, hoy amenazado por ciclones, cabras y conflicto geopolítico.",
    q: [
      "Por qué el aislamiento genera endemismos tan altos",
      "El árbol de sangre de dragón: usos históricos de su resina",
      "Amenazas actuales: ciclones de 2015, pastoreo y turismo"
    ]
  },
  {
    t: "Las minas de Naica",
    c: "Lugares",
    h: "Una cueva con cristales de yeso de once metros, a 58 °C y 100 % de humedad. Entrar sin traje mata en minutos.",
    d: "En Chihuahua, la Cueva de los Cristales estuvo inundada de agua saturada de sulfato de calcio a temperatura casi constante durante cientos de miles de años, lo que permitió crecimientos gigantescos. Se descubrió al bombear el agua para minar. Al cesar el bombeo, la cueva volvió a inundarse y hoy es inaccesible.",
    q: [
      "Qué condiciones permiten cristales de ese tamaño",
      "Microorganismos hallados atrapados dentro de los cristales",
      "Por qué se decidió reinundar la cueva"
    ]
  },
  {
    t: "Los relámpagos del Catatumbo",
    c: "Lugares",
    h: "Una tormenta en el mismo punto casi 300 noches al año, durante horas, sin apenas trueno audible.",
    d: "En la desembocadura del río Catatumbo, en el lago de Maracaibo, la topografía encierra aire húmedo del Caribe contra los Andes y genera tormentas nocturnas casi permanentes. Se ven a cientos de kilómetros y sirvieron de faro a los navegantes. Su frecuencia lo convierte en el lugar con más rayos por km² del mundo.",
    q: [
      "Mecanismo meteorológico: brisa de lago, orografía y convección nocturna",
      "Por qué se llegó a creer erróneamente que influía el metano",
      "Cómo se mide la densidad de rayos desde satélite"
    ]
  },
  {
    t: "Los puentes vivos de Meghalaya",
    c: "Lugares",
    h: "Puentes hechos guiando raíces de árbol durante décadas. Se fortalecen con el tiempo en vez de deteriorarse.",
    d: "El pueblo khasi conduce las raíces aéreas de Ficus elastica sobre andamios de bambú a través de ríos. Tardan entre 15 y 30 años en ser transitables y luego duran siglos, resistiendo monzones que se llevan cualquier estructura de acero. Es infraestructura viva y multigeneracional.",
    q: [
      "Cómo se guían las raíces y por qué se autorreparan (inosculación)",
      "Estudios de ingeniería que los analizan como estructuras",
      "Otras arquitecturas vivas: baubotanik y arboricultura estructural"
    ]
  },
  {
    t: "El Punto Nemo",
    c: "Lugares",
    h: "El lugar más alejado de tierra firme del planeta. Los humanos más cercanos suelen ir a bordo de la ISS.",
    d: "En el Pacífico Sur, a 2.688 km de cualquier costa, está el polo de inaccesibilidad oceánica. Es una zona de muy baja productividad biológica, dentro del giro del Pacífico Sur, y por eso se usa como cementerio de naves espaciales: allí se hunden los satélites y estaciones al reentrar.",
    q: [
      "Cómo se calcula un polo de inaccesibilidad",
      "El cementerio de naves espaciales y qué reposa allí",
      "El sonido 'Bloop' registrado cerca y su explicación real"
    ]
  }
];
