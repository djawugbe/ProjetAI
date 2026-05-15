import streamlit as st
import pandas as pd
import numpy as np
import json
from io import BytesIO
import plotly.express as px
import plotly.graph_objects as go

# =========================================================
# CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="DataGlance AI Pro",
    layout="wide",
    page_icon="✨",
    initial_sidebar_state="expanded"
)

# =========================================================
# STYLE CSS
# =========================================================
st.markdown(
    """
    <style>
    .main {
        background-color: #f8fafc;
    }

    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3em;
        background: linear-gradient(90deg, #4F46E5, #7C3AED);
        color: white;
        font-weight: bold;
        border: none;
        transition: 0.3s;
    }

    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 5px 15px rgba(0,0,0,0.15);
    }

    .metric-card {
        padding: 15px;
        border-radius: 15px;
        background: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }

    .title {
        text-align: center;
        color: #1E1B4B;
        font-size: 3rem;
        font-weight: bold;
    }

    .subtitle {
        text-align: center;
        color: #6B7280;
        font-size: 1.2rem;
        margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# FONCTIONS UTILITAIRES
# =========================================================

def load_data(uploaded_file):
    """Charge différents formats de fichiers."""
    try:
        name = uploaded_file.name.lower()

        if name.endswith('.csv'):
            return pd.read_csv(uploaded_file)

        elif name.endswith(('.xlsx', '.xls')):
            return pd.read_excel(uploaded_file)

        elif name.endswith('.json'):
            data = json.load(uploaded_file)
            return pd.json_normalize(data)

        else:
            st.error("Format non supporté.")
            return None

    except Exception as e:
        st.error(f"Erreur lors du chargement : {e}")
        return None


def detect_pii(df):
    """Détecte les colonnes contenant potentiellement des données sensibles."""

    keywords = [
        'nom', 'name', 'email', 'mail', 'phone', 'tel',
        'adresse', 'address', 'iban', 'password', 'pass',
        'salary', 'salaire', 'credit', 'card', 'cin',
        'passport', 'ssn', 'bank'
    ]

    pii_columns = []

    for col in df.columns:
        col_lower = col.lower()

        if any(keyword in col_lower for keyword in keywords):
            pii_columns.append(col)

    return pii_columns


def smart_clean(df):
    """Nettoyage intelligent des données."""

    def smart_clean(df):

    new_df = df.copy()

    for col in new_df.columns:

        if new_df[col].isnull().sum() > 0:

            if new_df[col].dtype == 'object':

                mode_value = new_df[col].mode()

                if not mode_value.empty:
                    new_df[col] = new_df[col].fillna(mode_value[0])

            else:

                median_value = new_df[col].median()

                new_df[col] = new_df[col].fillna(median_value)

    object_cols = new_df.select_dtypes(include=['object']).columns

    for col in object_cols:

        new_df[col] = (
            new_df[col]
            .astype(str)
            .str.strip()
            .str.replace(r'\\s+', ' ', regex=True)
        )

    new_df = new_df.drop_duplicates()

    return new_df

def anonymize_column(value):
    """Masque les données sensibles."""

    value = str(value)

    if len(value) <= 4:
        return '****'

    return value[:2] + '****' + value[-2:]


def convert_df_to_excel(df):
    """Convertit un DataFrame en Excel."""

    output = BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Data')

    return output.getvalue()


# =========================================================
# INITIALISATION SESSION
# =========================================================
if 'df' not in st.session_state:
    st.session_state.df = None

if 'original_df' not in st.session_state:
    st.session_state.original_df = None

# =========================================================
# HEADER
# =========================================================
st.markdown('<div class="title">✨ DataGlance AI Pro</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Analyse intelligente • Nettoyage automatique • Visualisation avancée</div>',
    unsafe_allow_html=True
)

st.divider()

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.image(
        "https://cdn-icons-png.flaticon.com/512/2092/2092663.png",
        width=120
    )

    st.header("📂 Chargement")

    uploaded_file = st.file_uploader(
        "Importer un fichier",
        type=['csv', 'xlsx', 'xls', 'json']
    )

    if uploaded_file is not None:

        # Recharger uniquement si nouveau fichier
        if (
            st.session_state.original_df is None or
            uploaded_file.name != st.session_state.get('current_file')
        ):

            loaded_df = load_data(uploaded_file)

            if loaded_df is not None:
                st.session_state.original_df = loaded_df.copy()
                st.session_state.df = loaded_df.copy()
                st.session_state.current_file = uploaded_file.name

        st.success("Fichier chargé avec succès")

        if st.button("🔄 Restaurer les données originales"):
            st.session_state.df = st.session_state.original_df.copy()
            st.success("Données restaurées")
            st.rerun()

# =========================================================
# APPLICATION PRINCIPALE
# =========================================================
if st.session_state.df is not None:

    df = st.session_state.df

    # =========================================================
    # METRICS DASHBOARD
    # =========================================================
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("📄 Lignes", df.shape[0])

    with col2:
        st.metric("📊 Colonnes", df.shape[1])

    with col3:
        missing_pct = round((df.isnull().sum().sum() / df.size) * 100, 2)
        st.metric("⚠️ Valeurs manquantes", f"{missing_pct}%")

    with col4:
        duplicates = df.duplicated().sum()
        st.metric("🧬 Doublons", duplicates)

    with col5:
        memory_usage = round(df.memory_usage(deep=True).sum() / 1024, 2)
        st.metric("💾 Mémoire", f"{memory_usage} KB")

    st.divider()

    # =========================================================
    # TABS
    # =========================================================
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔍 Analyse",
        "🛡️ Privacy",
        "⚡ Nettoyage",
        "📊 Visualisation",
        "📤 Export"
    ])

    # =========================================================
    # TAB ANALYSE
    # =========================================================
    with tab1:

        st.subheader("📋 Aperçu des données")
        st.dataframe(df.head(20), use_container_width=True)

        st.subheader("📑 Informations sur le dataset")

        info_df = pd.DataFrame({
            'Colonne': df.columns,
            'Type': df.dtypes.astype(str),
            'Valeurs manquantes': df.isnull().sum().values,
            'Valeurs uniques': [df[col].nunique() for col in df.columns]
        })

        st.dataframe(info_df, use_container_width=True)

        # Filtrage
        st.subheader("🔎 Filtrage intelligent")

        selected_column = st.selectbox(
            "Choisir une colonne",
            df.columns
        )

        if selected_column:

            unique_values = df[selected_column].dropna().unique()

            if len(unique_values) < 50:

                selected_values = st.multiselect(
                    "Filtrer les valeurs",
                    unique_values,
                    default=list(unique_values[:5]) if len(unique_values) > 5 else list(unique_values)
                )

                if selected_values:
                    filtered_df = df[df[selected_column].isin(selected_values)]
                    st.write(f"Résultats filtrés : {filtered_df.shape[0]} lignes")
                    st.dataframe(filtered_df, use_container_width=True)

    # =========================================================
    # TAB PRIVACY
    # =========================================================
    with tab2:

        st.subheader("🛡️ Détection des données sensibles")

        pii_cols = detect_pii(df)

        if pii_cols:

            st.warning(
                f"{len(pii_cols)} colonnes sensibles détectées"
            )

            st.write("Colonnes identifiées :")
            st.write(pii_cols)

            cols_to_hide = st.multiselect(
                "Colonnes à anonymiser",
                pii_cols,
                default=pii_cols
            )

            if st.button("🔐 Lancer l'anonymisation"):

                anonymized_df = df.copy()

                for col in cols_to_hide:
                    anonymized_df[col] = anonymized_df[col].apply(anonymize_column)

                st.session_state.df = anonymized_df

                st.success("Anonymisation terminée")
                st.balloons()
                st.rerun()

        else:
            st.success("Aucune donnée sensible détectée")

    # =========================================================
    # TAB NETTOYAGE
    # =========================================================
    with tab3:

        st.subheader("🤖 Nettoyage intelligent")

        st.markdown("""
        ### Actions disponibles

        - Imputation automatique des valeurs manquantes
        - Suppression des doublons
        - Normalisation des chaînes de caractères
        - Optimisation des données
        """)

        if st.button("🚀 Exécuter le nettoyage"):

            with st.spinner("Analyse et nettoyage en cours..."):

                cleaned_df = smart_clean(df)
                st.session_state.df = cleaned_df

                removed_duplicates = df.shape[0] - cleaned_df.shape[0]

                st.success("Nettoyage terminé avec succès")

                st.info(
                    f"{removed_duplicates} doublons supprimés"
                )

                st.rerun()

    # =========================================================
    # TAB VISUALISATION
    # =========================================================
    with tab4:

        st.subheader("📊 Analyse visuelle")

        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
        categorical_cols = df.select_dtypes(include='object').columns.tolist()

        if numeric_cols:

            st.markdown("### 📈 Histogramme")

            hist_col = st.selectbox(
                "Choisir une colonne numérique",
                numeric_cols,
                key='hist'
            )

            fig_hist = px.histogram(df, x=hist_col)
            st.plotly_chart(fig_hist, use_container_width=True)

            if len(numeric_cols) >= 2:

                st.markdown("### 📉 Corrélation")

                x_axis = st.selectbox(
                    "Axe X",
                    numeric_cols,
                    key='x_axis'
                )

                y_axis = st.selectbox(
                    "Axe Y",
                    numeric_cols,
                    key='y_axis'
                )

                fig_scatter = px.scatter(df, x=x_axis, y=y_axis)
                st.plotly_chart(fig_scatter, use_container_width=True)

                corr = df[numeric_cols].corr()

                heatmap = go.Figure(
                    data=go.Heatmap(
                        z=corr.values,
                        x=corr.columns,
                        y=corr.columns
                    )
                )

                st.markdown("### 🔥 Heatmap de corrélation")
                st.plotly_chart(heatmap, use_container_width=True)

        else:
            st.info("Aucune colonne numérique disponible")

        if categorical_cols:

            st.markdown("### 🥧 Répartition des catégories")

            cat_col = st.selectbox(
                "Choisir une colonne catégorielle",
                categorical_cols,
                key='cat'
            )

            value_counts = df[cat_col].value_counts().head(10)

            fig_pie = px.pie(
                names=value_counts.index,
                values=value_counts.values
            )

            st.plotly_chart(fig_pie, use_container_width=True)

    # =========================================================
    # TAB EXPORT
    # =========================================================
    with tab5:

        st.subheader("📤 Exportation des données")

        export_format = st.radio(
            "Choisir un format",
            ['CSV', 'Excel', 'JSON'],
            horizontal=True
        )

        if export_format == 'CSV':

            csv_data = df.to_csv(index=False).encode('utf-8')

            st.download_button(
                label='⬇️ Télécharger CSV',
                data=csv_data,
                file_name='dataglance_export.csv',
                mime='text/csv'
            )

        elif export_format == 'Excel':

            excel_data = convert_df_to_excel(df)

            st.download_button(
                label='⬇️ Télécharger Excel',
                data=excel_data,
                file_name='dataglance_export.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

        elif export_format == 'JSON':

            json_data = df.to_json(
                orient='records',
                indent=4
            )

            st.download_button(
                label='⬇️ Télécharger JSON',
                data=json_data,
                file_name='dataglance_export.json',
                mime='application/json'
            )

else:

    st.markdown(
        """
        <div style="text-align:center; padding:100px;">
            <img src="https://cdn-icons-png.flaticon.com/512/6165/6165577.png"
                 width="220"
                 style="opacity:0.5;">

            <h2 style="color:#64748B; margin-top:20px;">
                Importez un fichier pour démarrer
            </h2>

            <p style="color:#94A3B8; font-size:18px;">
                CSV • Excel • JSON
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
