import cloudscraper
from bs4 import BeautifulSoup
import time
from random import randint
import csv

#CONFIGURAÇÕES GERAIS

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/141.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "pt-PT,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.google.com/",
    "Connection": "keep-alive",
}

scraper = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "darwin", "mobile": False})

SCENARIOS = [
    {
        "name": "madrid_menores_precos",
        "descricao": "Primeiros 60 resultados mais baratos em Madrid",
        "first_page": "https://www.idealista.com/alquiler-viviendas/madrid-madrid/?ordenado-por=precios-asc",
        "page_template": "https://www.idealista.com/alquiler-viviendas/madrid-madrid/pagina-{page}.htm?ordenado-por=precios-asc",
        "max_pages": 60,
    },
    {
        "name": "madrid_maiores_precos",
        "descricao": "Primeiros 60 resultados mais caros em Madrid",
        "first_page": "https://www.idealista.com/alquiler-viviendas/madrid-madrid/?ordenado-por=precios-desc",
        "page_template": "https://www.idealista.com/alquiler-viviendas/madrid-madrid/pagina-{page}.htm?ordenado-por=precios-desc",
        "max_pages": 60,
    },
    {
        "name": "madrid_faixa_1300_3200",
        "descricao": "Resultados entre 1300€ e 3200€ ordenados por menor preço",
        "first_page": "https://www.idealista.com/alquiler-viviendas/madrid-madrid/con-precio-hasta_3200,precio-desde_1300/?ordenado-por=precios-asc",
        "page_template": "https://www.idealista.com/alquiler-viviendas/madrid-madrid/con-precio-hasta_3200,precio-desde_1300/pagina-{page}.htm?ordenado-por=precios-asc",
        "max_pages": 60,
    },
    {
        "name": "madrid_faixa_1600_3200",
        "descricao": "Resultados entre 1600€ e 3200€ ordenados por menor preço",
        "first_page": "https://www.idealista.com/alquiler-viviendas/madrid-madrid/con-precio-hasta_3200,precio-desde_1600/?ordenado-por=precios-asc",
        "page_template": "https://www.idealista.com/alquiler-viviendas/madrid-madrid/con-precio-hasta_3200,precio-desde_1600/pagina-{page}.htm?ordenado-por=precios-asc",
        "max_pages": 60,
    },
    {
        "name": "madrid_faixa_2000_3200",
        "descricao": "Resultados entre 2000€ e 3200€ ordenados por menor preço",
        "first_page": "https://www.idealista.com/alquiler-viviendas/madrid-madrid/con-precio-hasta_3200,precio-desde_2000/?ordenado-por=precios-asc",
        "page_template": "https://www.idealista.com/alquiler-viviendas/madrid-madrid/con-precio-hasta_3200,precio-desde_2000/pagina-{page}.htm?ordenado-por=precios-asc",
        "max_pages": 60,
    },
    {
        "name": "madrid_faixa_2725_3200",
        "descricao": "Resultados entre 2725€ e 3200€ ordenados por menor preço",
        "first_page": "https://www.idealista.com/alquiler-viviendas/madrid-madrid/con-precio-hasta_3200,precio-desde_2725/?ordenado-por=precios-asc",
        "page_template": "https://www.idealista.com/alquiler-viviendas/madrid-madrid/con-precio-hasta_3200,precio-desde_2725/pagina-{page}.htm?ordenado-por=precios-asc",
        "max_pages": 24,
    },
]


def fetch_page(url, retries=3, timeout=20):
    for attempt in range(retries):
        try:
            response = scraper.get(url, headers=HEADERS, timeout=timeout)
            response.raise_for_status()
            return response.text
        except Exception as exc:
            print(f"Tentativa {attempt + 1}/{retries} falhou para {url}: {exc}")
            if attempt == retries - 1:
                return None
            time.sleep(3)


def parse_html(html, tag="article", div_class="item"):
    soup = BeautifulSoup(html, "html.parser")
    divs = soup.find_all(tag, class_=div_class)
    return divs


def extract_content(divs):
    content_list = []
    for div in divs:
        try:
            title_tag = div.find("a", class_="item-link")
            title = title_tag.get_text(strip=True) if title_tag else "N/A"
            link = title_tag["href"] if title_tag and title_tag.has_attr("href") else ""
            if link and not link.startswith("http"):
                link = f"https://www.idealista.com{link}"

            price_tag = div.find("span", class_="item-price")
            price = price_tag.get_text(strip=True).replace("€", "").strip() if price_tag else "N/A"

            details = [d.get_text(strip=True) for d in div.find_all("span", class_="item-detail")]
            details_text = ", ".join(details) if details else "N/A"

            location_tag = div.find("span", class_="item-link")
            location = location_tag.get_text(strip=True) if location_tag else "Madrid"

            content_list.append(
                {
                    "titulo": title,
                    "preco (€)": price,
                    "detalhes": details_text,
                    "localizacao": location,
                    "link": link,
                }
            )

        except Exception as e:
            print(f"Erro ao extrair item: {e}")
            continue
    return content_list


def list_to_csv(data, csv_filename):
    if not data:
        print("Nenhum dado para salvar.")
        return

    fieldnames = data[0].keys()
    try:
        with open(csv_filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        print(f"Arquivo CSV '{csv_filename}' criado com sucesso!")
    except Exception as e:
        print(f"Erro ao salvar CSV: {e}")


def random_sleep():
    delay = randint(2, 5)
    print(f"Aguardando {delay}s para evitar bloqueio...")
    time.sleep(delay)


def build_url_for_page(config: dict, page: int) -> str:
    if page <= 1:
        return config["first_page"]
    return config["page_template"].format(page=page)


def get_div_content(url, tag="article", div_class="item"):
    page_content = fetch_page(url)
    if not page_content:
        print("Falha ao carregar página da web.")
        return []

    divs = parse_html(page_content, tag, div_class)
    content = extract_content(divs)
    return content


def scrape_properties(config: dict, seen_items: set, results: list, csv_filename=None):
    print(f"\n=== Iniciando cenário: {config['name']} ({config['descricao']}) ===")

    for page in range(1, config["max_pages"] + 1):
        url = build_url_for_page(config, page)
        print(f"Scraping {url}...")
        content = get_div_content(url)

        if not content:
            print("Nenhum conteúdo encontrado; encerrando este cenário.")
            break

        unique_content = []
        for item in content:
            key = item.get("link")
            if key and key not in seen_items:
                seen_items.add(key)
                unique_content.append(item)

        if unique_content:
            results.extend(unique_content)
            if csv_filename:
                list_to_csv(results, csv_filename)
        else:
            print("Somente itens já coletados nesta página.")

        random_sleep()

    return results


if __name__ == "__main__":
    all_results = []
    seen_links = set()

    for scenario in SCENARIOS:
        all_results = scrape_properties(
            scenario,
            seen_links,
            all_results,
            csv_filename="idealista_madrid.csv",
        )

    if not all_results:
        print("Nenhum dado coletado na raspagem.")
    else:
        print(f"Total de imóveis coletados: {len(all_results)}")

