import re
from typing import Optional, Tuple

import pandas as pd


def load_idealista_data(csv_path: str = "idealista_lisboa.csv") -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    if "link" in df.columns:
        original_len = len(df)
        df = df.drop_duplicates(subset="link")
        removed = original_len - len(df)
        if removed:
            print(f"Registros duplicados removidos com base no link: {removed}")

    if "preco (€)" in df.columns:
        df["preco (€)"] = (
            df["preco (€)"]
            .astype(str)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
            .str.replace(r"[^\d.]", "", regex=True)
            .replace("", pd.NA)
            .astype(float)
        )

    if "detalhes" in df.columns:
        df["tipo"] = df["detalhes"].apply(extract_tipo)
        df["metragem (m²)"] = df["detalhes"].apply(extract_metragem)

    if {"preco (€)", "metragem (m²)"}.issubset(df.columns):
        df["preco por m² (€)"] = df.apply(compute_price_per_sqm, axis=1)

    if {"localizacao", "titulo"}.issubset(df.columns):
        bairros_freguesias = df.apply(extract_bairro_freguesia, axis=1)
        df["bairro"] = bairros_freguesias.apply(lambda pair: pair[0])
        df["freguesia"] = bairros_freguesias.apply(lambda pair: pair[1])

    return df


def extract_tipo(details: str) -> Optional[str]:
    if not isinstance(details, str) or not details.strip():
        return None

    primary = details.split(",")[0].strip()
    if not primary:
        return None

    normalized = primary.upper()
    valid_prefixes = ("T0", "T1", "T2", "T3", "T4", "T5", "T6", "T7")
    if normalized.startswith(valid_prefixes):
        return normalized[:2]  # mantém formato Tn

    keywords = [
        "MORADIA",
        "APARTAMENTO",
        "ESTÚDIO",
        "ESTUDIO",
        "QUARTO",
        "DUPLEX",
    ]
    for keyword in keywords:
        if keyword in normalized:
            return keyword.title()

    return primary.title()


def extract_metragem(details: str) -> Optional[float]:
    if not isinstance(details, str):
        return None

    match = re.search(r"(\d+[\.,]?\d*)\s*m", details, re.IGNORECASE)
    if not match:
        return None

    value = match.group(1).replace(".", "").replace(",", ".")
    try:
        return float(value)
    except ValueError:
        return None


def save_clean_csv(df: pd.DataFrame, output_path: str = "idealista_lisboa_tratado.csv") -> None:
    df.to_csv(output_path, index=False)
    print(f"Arquivo tratado salvo em: {output_path}")


def clean_location_fragment(fragment: str) -> Optional[str]:
    fragment = fragment.strip()
    if not fragment or fragment.isdigit():
        return None

    if any(char.isdigit() for char in fragment):
        # ignora trechos claramente numéricos (n.º, códigos postais)
        return None

    fragment = fragment.replace("–", "-").replace("—", "-")
    fragment = re.sub(r"\s+", " ", fragment)
    fragment = fragment.replace("-", " - ").strip()

    if not fragment:
        return None

    normalized = fragment.title()
    if normalized.lower() in {"lisboa", "portugal"}:
        return None

    return normalized


def compute_price_per_sqm(row: pd.Series) -> Optional[float]:
    price = row.get("preco (€)")
    size = row.get("metragem (m²)")

    if price is None or size in (None, 0):
        return None

    try:
        return float(price) / float(size)
    except (TypeError, ZeroDivisionError, ValueError):
        return None


def parse_location_text(text: str) -> tuple[Optional[str], Optional[str]]:
    if not isinstance(text, str) or not text.strip():
        return None, None

    parts = [segment.strip() for segment in text.split(",") if segment.strip()]
    if not parts:
        return None, None

    freguesia_raw = clean_location_fragment(parts[-1]) or parts[-1].title()

    bairro = None
    for candidate in reversed(parts[:-1]):
        cleaned = clean_location_fragment(candidate)
        if cleaned:
            bairro = cleaned
            break

    if not freguesia_raw and bairro:
        freguesia_raw = bairro

    return bairro, freguesia_raw


def extract_bairro_freguesia(row: pd.Series) -> tuple[Optional[str], Optional[str]]:
    texts = []
    for key in ("localizacao", "titulo"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            texts.append(value.replace("–", "-").replace("—", "-"))

    fallback: Tuple[Optional[str], Optional[str]] = (None, None)

    for text in texts:
        bairro, freguesia = parse_location_text(text)
        if bairro and freguesia:
            return bairro, freguesia
        if freguesia and fallback == (None, None):
            fallback = (freguesia, freguesia)

    return fallback


def main():
    df = load_idealista_data()
    print("Pré-visualização dos dados:")
    print(df.head())
    print("\nInformações gerais:")
    print(df.info())
    if "preco (€)" in df.columns:
        print("\nResumo estatístico do preço (€):")
        print(df["preco (€)"].describe())
    if "metragem (m²)" in df.columns:
        print("\nResumo estatístico da metragem (m²):")
        print(df["metragem (m²)"].describe())
    if "bairro" in df.columns:
        print("\nBairros mais comuns:")
        print(df["bairro"].value_counts().head(10))

    save_clean_csv(df)


if __name__ == "__main__":
    main()

