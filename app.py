import streamlit as st
import pandas as pd
import numpy as np

def process_file(uploaded_file):
    """Charge et traite le fichier CSV exporté"""
    try:
        # Essayer d'abord UTF-16, puis UTF-8 si échec
        try:
            df = pd.read_csv(
                uploaded_file,
                sep='\t',
                encoding='utf-16',
                quoting=3
            )
        except UnicodeError:
            uploaded_file.seek(0)  # Retour au début du fichier
            df = pd.read_csv(
                uploaded_file,
                sep='\t',
                encoding='utf-8',
                quoting=3
            )
        
        # Sélectionner et renommer les colonnes pertinentes avec les noms exacts
        df_cleaned = df[[
            '"Keyword"', '"Volume"', '"Current position"', '"Current URL"',
            '"Branded"', '"Local"', '"Informational"', '"Commercial"', '"Transactional"'
        ]].rename(columns={
            '"Keyword"': 'keyword',
            '"Volume"': 'volume',
            '"Current position"': 'position',
            '"Current URL"': 'url',
            '"Branded"': 'branded',
            '"Local"': 'local',
            '"Informational"': 'informational',
            '"Commercial"': 'commercial',
            '"Transactional"': 'transactional'
        })
        
        # Nettoyage des données
        for col in df_cleaned.columns:
            if df_cleaned[col].dtype == 'object':
                df_cleaned[col] = df_cleaned[col].str.strip('"')
        
        # Conversion des types
        df_cleaned['volume'] = pd.to_numeric(df_cleaned['volume'].str.replace(',', ''), errors='coerce')
        df_cleaned['position'] = pd.to_numeric(df_cleaned['position'], errors='coerce')
        
        return df_cleaned
        
    except Exception as e:
        st.error(f"Erreur lors du chargement: {str(e)}")
        if 'df' in locals():
            st.write("Colonnes disponibles:", df.columns.tolist())
        return None

def cluster_keywords(df):
    """Regroupe et analyse les mots-clés par URL"""
    try:
        # Tri par volume décroissant
        df_sorted = df.sort_values(by='volume', ascending=False)
        
        # Création d'un dictionnaire pour stocker les top keywords et leurs volumes
        top_keywords = {}
        top_volumes = {}
        for url in df_sorted['url'].unique():
            url_df = df_sorted[df_sorted['url'] == url]
            if not url_df.empty:
                top_keywords[url] = url_df.iloc[0]['keyword']
                top_volumes[url] = int(url_df.iloc[0]['volume'])
        
        # Groupement par URL
        grouped = df_sorted.groupby('url', as_index=False).agg({
            'keyword': list,
            'position': list,
            'volume': list
        })
        
        # Calcul des métriques
        grouped['keyword_count'] = grouped['keyword'].apply(len)
        grouped['total_volume'] = grouped['volume'].apply(sum)
        grouped['avg_position'] = grouped['position'].apply(lambda x: round(sum(x)/len(x), 1))
        
        # Ajout du top keyword et son volume
        grouped['top_keyword'] = grouped['url'].map(top_keywords)
        grouped['top_keyword_volume'] = grouped['url'].map(top_volumes)
        
        # Formatage des listes en texte avec retours à la ligne
        grouped['keyword'] = grouped['keyword'].apply(lambda x: '\n'.join(str(k) for k in x))
        grouped['position'] = grouped['position'].apply(lambda x: '\n'.join(str(p) for p in x))
        grouped['volume'] = grouped['volume'].apply(lambda x: '\n'.join(str(int(v)) for v in x))
        
        # Réorganisation des colonnes selon le format demandé
        result = grouped[[
            'url',
            'top_keyword',
            'top_keyword_volume',
            'avg_position',
            'keyword_count',
            'total_volume',
            'keyword',
            'volume',
            'position'
        ]]
        
        # Tri par volume du top mot-clé (ordre croissant)
        result = result.sort_values(by='top_keyword_volume', ascending=True)
        
        return result
    
    except Exception as e:
        st.error(f"Erreur lors du clustering: {str(e)}")
        return None

def main():
    # Configuration de la page
    st.set_page_config(
        page_title="Analyse SEO Avancée",
        page_icon="🎯",
        layout="wide"
    )

    # CSS personnalisé
    st.markdown("""
        <style>
        /* Couleur des titres */
        h1, h2, h3 {
            color: #5C6CA1;
        }
        
        /* Style du bouton principal */
        .stButton>button {
            background-color: #2BAF9C;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 0.5rem 1rem;
        }
        
        .stButton>button:hover {
            background-color: #58C4B7;
        }
        
        /* Style des métriques */
        [data-testid="metric-container"] {
            background-color: #B6CFF2;
            padding: 1rem;
            border-radius: 4px;
        }
        
        /* Style du séparateur */
        hr {
            border-color: #FFA59D;
        }
        
        /* Style de la sidebar */
        [data-testid="stSidebar"] {
            background-color: #CBDCEA;
        }
        </style>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.title("🎯 Analyse SEO")
        
        st.markdown("""
        ### Mode d'emploi
        
        1️⃣ **Upload du fichier**
        - Format accepté : CSV tabulé
        - Encodage : UTF-8 ou UTF-16
        
        2️⃣ **Analyse automatique**
        - Clustering par URL
        - Calcul des métriques
        - Tri par volume
        
        3️⃣ **Export des résultats**
        - Format CSV (séparateur ;)
        - Colonnes renommées
        """)
        
        # Zone de drag & drop
        st.markdown("### 📂 Import du fichier")
        uploaded_file = st.file_uploader(
            "Déposez votre fichier CSV",
            type=['csv'],
            help="Fichier CSV exporté avec séparateur tabulation"
        )

    # Zone principale
    if uploaded_file:
        with st.spinner("⏳ Analyse en cours..."):
            df = process_file(uploaded_file)
            if df is not None:
                results = cluster_keywords(df)
                
                if results is not None:
                    # Statistiques en colonnes
                    st.markdown("### 📊 Statistiques générales")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(
                            "Nombre de mots-clés",
                            len(df),
                            help="Nombre total de mots-clés analysés"
                        )
                    with col2:
                        st.metric(
                            "Volume total",
                            f"{df['volume'].sum():,.0f}",
                            help="Somme des volumes de recherche"
                        )
                    with col3:
                        st.metric(
                            "Position moyenne",
                            f"{df['position'].mean():.1f}",
                            help="Position moyenne tous mots-clés confondus"
                        )
                    
                    # Séparateur
                    st.markdown("---")
                    
                    # Résultats
                    st.markdown("### 🔍 Résultats de l'analyse")
                    
                    # Définition des noms de colonnes pour l'export
                    column_names = {
                        "url": "URL",
                        "top_keyword": "Top mot-clé",
                        "top_keyword_volume": "Volume du top mot-clé",
                        "avg_position": "Position moyenne",
                        "keyword_count": "Nb mots-clés",
                        "total_volume": "Volume total",
                        "keyword": "Mots-clés",
                        "volume": "Volumes",
                        "position": "Positions"
                    }
                    
                    # Configuration de l'affichage
                    st.dataframe(
                        results,
                        column_config={
                            "url": st.column_config.TextColumn(
                                "URL",
                                help="URL de la page analysée"
                            ),
                            "top_keyword": st.column_config.TextColumn(
                                "Top mot-clé",
                                help="Mot-clé avec le plus grand volume"
                            ),
                            "top_keyword_volume": st.column_config.NumberColumn(
                                "Volume du top mot-clé",
                                help="Volume de recherche du top mot-clé",
                                format="%d"
                            ),
                            "avg_position": st.column_config.NumberColumn(
                                "Position moyenne",
                                help="Position moyenne de la page",
                                format="%.1f"
                            ),
                            "keyword_count": st.column_config.NumberColumn(
                                "Nb mots-clés",
                                help="Nombre de mots-clés total"
                            ),
                            "total_volume": st.column_config.NumberColumn(
                                "Volume total",
                                help="Somme des volumes de recherche",
                                format="%d"
                            ),
                            "keyword": st.column_config.TextColumn(
                                "Mots-clés",
                                help="Liste des mots-clés"
                            ),
                            "volume": st.column_config.TextColumn(
                                "Volumes",
                                help="Volumes de recherche correspondants"
                            ),
                            "position": st.column_config.TextColumn(
                                "Positions",
                                help="Positions correspondantes"
                            )
                        },
                        height=600,
                        use_container_width=True
                    )
                    
                    # Export
                    st.markdown("### 💾 Exporter les résultats")
                    results_export = results.rename(columns=column_names)
                    st.download_button(
                        "📥 Télécharger l'analyse complète",
                        results_export.to_csv(index=False, sep=';'),
                        "analyse_seo_complete.csv",
                        "text/csv",
                        key='download-csv',
                        help="Télécharger les résultats au format CSV"
                    )

if __name__ == "__main__":
    main() 