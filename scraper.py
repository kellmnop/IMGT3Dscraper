import os
import io
import requests
import argparse
from bs4 import BeautifulSoup
import pandas

'''
All the form options are hardcoded, which isn't ideal.
'''

receptor_types = ('any', 'IG', 'TR', 'MH', 'RPI', 'FPIA', 'CPCA', 'any', 'MH1', 'MH2', 'RPI-MH1Like', 'FV', 'SCFV', 'FAB', 'FC') # ReceptorType
complex_types = ('any', 'IG/Ag', 'TR/peptide/MH1', 'TR/peptide/MH2', 'RPI/peptide/MH1', 'RPI/peptide/MH2', 'peptide/MH1', 'peptide/MH2') # also ReceptorType

species = ('any', 'Adeno-associated virus - 2', 'Aeromonas hydrophila', 'Anasplatyrhunchos', 'Bos taurus', 'Branchiostoma floridae', 
           'Caenorhabditis elegans', 'Camelus dromedarius', 'Caninized', 'Canis lupus familiaris', 'Cavia porcellus', 
           'Chimeric', 'Corynebacterium diphtheriae', 'Cricetinae gen. sp.', 'Ctenopharyngodon idella', 'Cytomegalovirus', 
           'Danio rerio', 'Dengue virus 4', 'Drosophila melanogaster', 'Eptatretus burgeri', 'Equus caballus', 
           'Escherichia coli', 'Felinized', 'Gallus gallus', 'Ginglymostoma cirratum', 'Gorilla', 'Heloderma suspectum', 
           'Homo sapiens', 'Human immunodeficiency virus 1', 'Humanized', 'Hyalophora cecropia', 'Ictalurus punctatus', 
           'Indiana vesiculovirus', 'Lama glama', 'Lampetra planeri', 'Lepus', 'Lethenteron camtschaticum', 'Macaca fascicularis', 
           'Macaca mulatta', 'Mus musculus', 'Mycobacterium tuberculosis', 'Orectolobus maculatus', 'Oryctolagus cuniculus', 
           'Petromyzon marinus', 'Pteropus alecto', 'Rattus norvegicus', 'Salmonella enterica', 
           'Severe acute respiratory syndrome coronavirus (SARS-CoV)', 'Squalus acanthias', 'Staphylococcus aureus', 
           'Sus scrofa', 'synthetic construct', 'Vicugna pacos', 'Xenopus laevis') # species

peptide_lengths = ('any', '0','1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19','20','21','22',
                   '23','24','25','26','28','29','30','31','33','34','35','36','37','40','42','45','46','55','60','71','72',
                   '76','82','86','89','93','101','106','114','127','129','132','133','139','153','154','156','160','163',
                   '176','179','183','189','190','221','222','223','227','230','235','240','255','256','257','262','267',
                   '270','271','274','296','305','310','313','322','327','329','332','344','353','373','398','407','479',
                   '483','518','573','606','631','649','660','697','739','927','941') # PepLength

class scraper:
    """
    A class to scrape protein overview data from the IMGT 3Dstructure-DB.
    Attributes:
        query_url (str): The URL endpoint for the IMGT 3Dstructure-DB query.
        headers (dict): HTTP headers to use for the POST request.
        params (dict): Query parameters for the POST request.
        outfile (str): Path to the output CSV file.
    Methods:
        get_query_params(args):
            Constructs and returns the query parameters dictionary based on user input.
        post_query():
            Sends a POST request to the IMGT 3Dstructure-DB and returns the HTML response content.
            Raises an exception if the request fails.
        process_response(html_content):
            Parses the HTML content and extracts the results table.
            Raises an exception if the results table is not found.
        run():
            Executes the full scraping process: sends the query, processes the response,
            converts the results to a DataFrame, and writes the output to a CSV file.
            Validates output directory permissions and handles file writing errors.
    """
    def __init__(self, params):
        self.query_url = "https://www.imgt.org/3Dstructure-DB/cgi/3Dquery.cgi"
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}      
        self.params = self.get_query_params(params)
        self.outfile = params['outfile']
    
    def get_query_params(self, args):
        params = {
            "type-result" : "ProteinOverview",
            "EntryGeneAllele" : "true", "type-entry" : "PDB",
            "ReceptorType": args['receptor'],
            "Species": args['species'],
            "PepLength": args['peptide_length']
        }
        return params
    
    def post_query(self):
        try:
            response = requests.post(self.query_url, data=self.params, headers=self.headers)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch data: {e}")
    
    def process_response(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        results_table = soup.select_one('table.Results')
        if results_table is None:
            raise Exception("No results table found in the response.")
        return results_table
    
    def run(self):
        html_content = self.post_query()
        if not html_content:
            raise Exception("No content returned from the query.")
        results_table = self.process_response(html_content)
        if results_table is None:
            raise Exception("No results table found in the response.")

        results_df = pandas.read_html(io.StringIO(str(results_table)), header=0, index_col=0)[0]

        # Validate if the output path is writable
        output_dir = os.path.dirname(self.outfile)
        if output_dir and not os.access(output_dir, os.W_OK):
            raise Exception(f"Output directory '{output_dir}' is not writable or does not exist.")

        try:
            results_df.to_csv(self.outfile, index=False)
        except (IOError, OSError) as e:
            raise Exception(f"Failed to write to file {self.outfile}: {e}")
        try:
            results_df.to_csv(self.outfile, index=False)
        except (IOError, OSError) as e:
            raise Exception(f"Failed to write to file {self.outfile}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query IMGT 3Dstructure-DB")
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--receptor', choices=(receptor_types+complex_types), default="any", help="Receptor type to search for. Can also specify complex type e.g. 'IG/Ag' or 'TR/peptide/MH1'")
    parser.add_argument('--species', choices=species, default="any", help="Species")
    parser.add_argument('--peptide_length', choices=peptide_lengths, default="any", help="Peptide length")
    parser.add_argument('--outfile', type=str, default="imgt_3dstructure_db_results.csv", help="Output file name for results")

    args = parser.parse_args()
    print(args)
    args_dict = vars(args)
    print(args_dict)
    imgt_scraper = scraper(args_dict)
    imgt_scraper.run()
