# Definició de Producte: Escolta Damm

## 1. El Problema (Pain Points)
El departament de People (RRHH) llança enquestes de clima, però s'enfronta a tres grans tensions:
* **Falta de representativitat:** Col·lectius clau com Planta i Logística responen menys que Oficina o Mànagers (bretxa digital i de temps).
* **Sobrecàrrega (Fatiga d'enquestes):** Les enquestes tradicionals són massa llargues i genèriques. No s'adapten a la realitat de cada col·lectiu.
* **Anàlisi tardana:** Per quan RRHH acaba de llegir centenars de comentaris oberts i agrupar-los per temàtiques, el problema ja ha mutat o la gent sent que "la seva opinió no serveix per a res".

## 2. Usuaris Objectiu (User Personas)
* **El Creador (Equip de People / RRHH):** Necessita llançar microconsultes en 2 minuts sense ser expert a redactar enquestes. Necessita veure tendències clares i proposar plans d'acció recolzats per dades.
* **El Participant (Ex. Operari de Planta):** No té ordinador corporatiu. Necessita escanejar un QR amb el seu mòbil, respondre en menys de 2 minuts, sentir que l'enquesta parla del seu dia a dia i tenir garanties absolutes d'anonimat.

## 3. Regles de Negoci i Privacitat (Guardrails)
Per garantir la confiança dels treballadors i la utilitat per a RRHH, el sistema es regeix per tres regles innegociables:

* **Regla 1: Privacitat i Validesa per Percentatge de Mostra (Llindar Dinàmic)**
  El sistema no utilitza un tall rígid de nombre de respostes, sinó un **llindar percentual adaptat a la grandària de cada col·lectiu** (Un mínim d'un 15% de participació sobre el cens total d'aquell grup). Si un segment no arriba a aquest percentatge relatiu, el sistema oculta automàticament els resultats per evitar biaixos estadístics i garantir l'anonimat matemàtic en equips petits.

* **Regla 2: IA Segura i Delimitada (Temes Prohibits)**
  La Intel·ligència Artificial no té llibertat absoluta; actua com un assistent guiat. Abans de generar qualsevol microconsulta, el sistema aplica un filtre de "línies vermelles" que impedeix formular preguntes sobre temes sensibles fora del control de clima (ex. salaris, acomiadaments, dades mèdiques). 

* **Regla 3: Transparència de Mostra (Alertes de Representativitat)**
  El tauler de comandament no enganya RRHH. Si un col·lectiu respon per sota del seu pes poblacional (ex. Planta només representa un 5% de la mostra quan són el 40% de la plantilla), el sistema no oculta el col·lectiu, sinó que l'etiqueta clarament com a "Infrarepresentat". L'insight per a RRHH aquí no és prendre decisions sobre els resultats, sinó llançar accions per millorar la participació d'aquell grup.