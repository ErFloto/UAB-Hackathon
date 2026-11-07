"""
Script independent per entrenar el model Naïve Bayes i guardar-lo per al seu ús.
Només cal executar-lo un cop (o quan hi hagi dades noves).
"""
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import joblib
from datos import generar_respostes, normalitza

print("Generant dades d'entrenament sintètiques...")
# Generem un volum més gran de respostes per a l'entrenament
df_train = generar_respostes(n=2000, seed=123)

# Filtrem només aquells que tenen comentari
df_train = df_train[df_train["comentari_obert"].astype(str).str.strip() != ""]

print(f"Entrenant model amb {len(df_train)} comentaris...")

# Normalitzem el text per l'entrenament (mateixa funció que usavem abans)
text_train = df_train["comentari_obert"].apply(normalitza)
y_tema = df_train["tema_real"]

# Convertim el text a vectors TF-IDF
vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=2)
X_train = vectorizer.fit_transform(text_train)

# Entrenem el classificador Naïve Bayes
model_nb = MultinomialNB(alpha=0.1) # Alpha < 1 sol anar millor per textos curts
model_nb.fit(X_train, y_tema)

# Guardem el model i el vectoritzador
print("Guardant el model a 'model_nb.joblib' i 'vectorizer.joblib'...")
joblib.dump(vectorizer, "vectorizer.joblib")
joblib.dump(model_nb, "model_nb.joblib")

print("Entrenament completat amb èxit!")
