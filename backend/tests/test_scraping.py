"""
Script de teste para scrapers.

Execute com: docker exec -it prospectai_backend python -m tests.test_scraping
"""

import asyncio
import sys
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_google_maps_scraper():
    """Testa o scraper do Google Maps."""
    from app.services.scraping import GoogleMapsScraper
    
    print("\n" + "="*60)
    print("TESTE: Google Maps Scraper")
    print("="*60)
    
    try:
        async with GoogleMapsScraper(headless=True) as scraper:
            result = await scraper.scrape(
                query="restaurantes",
                location="São Paulo, SP",
                limit=5
            )
            
            print(f"\n✓ Status: {'Sucesso' if result.success else 'Erro'}")
            print(f"✓ Query: {result.query}")
            print(f"✓ Location: {result.location}")
            print(f"✓ Total encontrado: {result.total_found}")
            print(f"✓ Duração: {result.duration_seconds}s")
            
            if result.error:
                print(f"✗ Erro: {result.error}")
            
            if result.businesses:
                print(f"\n📋 Negócios encontrados:")
                for i, biz in enumerate(result.businesses, 1):
                    print(f"\n  {i}. {biz.name}")
                    if biz.address:
                        print(f"     📍 {biz.address}")
                    if biz.phone:
                        print(f"     📞 {biz.phone}")
                    if biz.website:
                        print(f"     🌐 {biz.website}")
                    if biz.rating:
                        print(f"     ⭐ {biz.rating} ({biz.reviews_count or 0} avaliações)")
            
            return result.success
            
    except Exception as e:
        print(f"\n✗ Erro no teste: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_google_scraper():
    """Testa o scraper do Google Search."""
    from app.services.scraping import GoogleScraper
    
    print("\n" + "="*60)
    print("TESTE: Google Search Scraper")
    print("="*60)
    
    try:
        async with GoogleScraper(headless=True) as scraper:
            result = await scraper.scrape(
                query="agências de marketing digital",
                location="São Paulo, SP",
                limit=5
            )
            
            print(f"\n✓ Status: {'Sucesso' if result.success else 'Erro'}")
            print(f"✓ Total encontrado: {result.total_found}")
            print(f"✓ Duração: {result.duration_seconds}s")
            
            if result.error:
                print(f"✗ Erro: {result.error}")
            
            if result.businesses:
                print(f"\n📋 Sites/empresas encontrados:")
                for i, biz in enumerate(result.businesses, 1):
                    print(f"\n  {i}. {biz.name}")
                    if biz.website:
                        print(f"     🌐 {biz.website}")
            
            return result.success
            
    except Exception as e:
        print(f"\n✗ Erro no teste: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_contact_extraction():
    """Testa extração de contatos de um website."""
    from app.services.scraping import GoogleScraper
    
    print("\n" + "="*60)
    print("TESTE: Extração de Contatos de Website")
    print("="*60)
    
    # Site de teste (página de contato típica)
    test_url = "https://www.sebrae.com.br/sites/PortalSebrae/faleconosco"
    
    try:
        async with GoogleScraper(headless=True) as scraper:
            contact = await scraper.extract_contact_from_website(test_url)
            
            if contact:
                print(f"\n✓ URL: {contact.source_url}")
                print(f"✓ Emails encontrados: {contact.emails}")
                print(f"✓ Telefones encontrados: {contact.phones}")
                print(f"✓ Redes sociais: {contact.social_media}")
                return True
            else:
                print(f"\n✗ Não foi possível extrair contatos de {test_url}")
                return False
            
    except Exception as e:
        print(f"\n✗ Erro no teste: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Executa todos os testes."""
    print("\n" + "#"*60)
    print("#" + " "*20 + "TESTES DE SCRAPING" + " "*20 + "#")
    print("#"*60)
    
    results = {
        "Google Maps": await test_google_maps_scraper(),
        "Google Search": await test_google_scraper(),
        "Contact Extraction": await test_contact_extraction(),
    }
    
    print("\n" + "="*60)
    print("RESUMO DOS TESTES")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        print(f"  {test_name}: {status}")
    
    passed_count = sum(results.values())
    total_count = len(results)
    
    print(f"\nTotal: {passed_count}/{total_count} testes passaram")
    
    return all(results.values())


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
