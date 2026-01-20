"""
Script de debug para scrapers.
Verifica o HTML retornado e salva screenshots.
"""

import asyncio
import sys
import os

# Adicionar o diretório do app ao path
sys.path.insert(0, '/app')

from app.services.scraping.google_scraper import GoogleScraper


async def debug_google_search():
    """Debug do Google Search para entender o HTML."""
    print("\n" + "=" * 60)
    print("DEBUG: Google Search")
    print("=" * 60)
    
    try:
        async with GoogleScraper(headless=True) as scraper:
            page = await scraper.new_page()
            
            # Acessar Google
            url = "https://www.google.com/search?q=restaurantes+em+São+Paulo&num=10"
            print(f"\n📡 Acessando: {url}")
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Salvar screenshot
            screenshot_path = "/tmp/google_search_debug.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"📸 Screenshot salvo: {screenshot_path}")
            
            # Salvar HTML
            html_path = "/tmp/google_search_debug.html"
            html_content = await page.content()
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"📄 HTML salvo: {html_path}")
            
            # Verificar título da página
            title = await page.title()
            print(f"\n📌 Título da página: {title}")
            
            # Verificar se há CAPTCHA ou bloqueio
            if "unusual traffic" in html_content.lower() or "captcha" in html_content.lower():
                print("⚠️  CAPTCHA ou bloqueio detectado!")
            
            # Tentar diferentes seletores
            selectors_to_test = [
                ('div.g', 'Resultado padrão'),
                ('div[data-hveid]', 'Data attribute'),
                ('div.MjjYud', 'Novo container'),
                ('div[jscontroller]', 'JS controller'),
                ('h3', 'Títulos h3'),
                ('a[href^="http"]', 'Links HTTP'),
                ('div.tF2Cxc', 'Container de resultado'),
                ('div.yuRUbf', 'Container de título'),
            ]
            
            print("\n🔍 Testando seletores:")
            for selector, desc in selectors_to_test:
                try:
                    elements = await page.query_selector_all(selector)
                    count = len(elements)
                    print(f"  {selector:30} ({desc:20}): {count} elementos")
                    
                    # Mostrar primeiros 3 textos se houver
                    if count > 0 and count <= 10:
                        for i, el in enumerate(elements[:3]):
                            text = await el.inner_text()
                            text = text[:80].replace('\n', ' ').strip()
                            print(f"    [{i}] {text}...")
                except Exception as e:
                    print(f"  {selector:30} ({desc:20}): ERRO - {e}")
            
            await page.close()
            print("\n✅ Debug concluído!")
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()


async def test_simple_website():
    """Testa extração de contatos de um site simples."""
    print("\n" + "=" * 60)
    print("TESTE: Extração de contatos de website simples")
    print("=" * 60)
    
    try:
        async with GoogleScraper(headless=True) as scraper:
            # Testar com um site mais leve
            test_url = "https://httpbin.org/html"
            
            print(f"\n📡 Acessando: {test_url}")
            page = await scraper.new_page()
            await page.goto(test_url, wait_until="networkidle", timeout=15000)
            
            html = await page.content()
            print(f"✅ HTML carregado: {len(html)} caracteres")
            
            await page.close()
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")


async def main():
    print("\n" + "#" * 60)
    print("#" + " " * 16 + "DEBUG DE SCRAPING" + " " * 17 + "#")
    print("#" * 60)
    
    await debug_google_search()
    await test_simple_website()


if __name__ == "__main__":
    asyncio.run(main())
