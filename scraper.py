import numpy as np
import requests
from bs4 import BeautifulSoup
from lxml import etree
from lxml import html
import time
import re

class WebScraper:
    def __init__(self):
        self.links = []
        self.root_element = etree.Element("matches")
        self.last_id = 0
        self.dict_teams = {}
        self.linksProcesador = 0
        
    def obtener_links_liga_campeones(self):
        url = "https://www.bdfutbol.com/es/t/t.html"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        seasons = soup.find_all("div", class_="item_temporada")

        temporadasAObtener = 93

        for i in range(temporadasAObtener):
            link = seasons[i].find('a', href=True)
            if link:
                self.links.append(link['href'])    
        print(self.links)

    def obtener_id(self, team_name):
        if not self.dict_teams.get(team_name) :
            self.dict_teams[team_name] = self.last_id
            self.last_id += 1
            return self.last_id
        else:
            return self.dict_teams.get(team_name)

    def crear_datos_partido(self, competicion, jornadasObtenidas, temporada, estadio, jornada_fecha, arbitro, equipo_local, equipo_visitante, goles_local, goles_visitante, goleadores):
        match_element = etree.Element("match")
        
        etree.SubElement(match_element, "competition").text = competicion
        etree.SubElement(match_element, "season").text = temporada
        etree.SubElement(match_element, "matchweek").text = str(jornadasObtenidas)

        if jornada_fecha == "sin dato":
            etree.SubElement(match_element, "date").text = "sin dato"
        else:
            fecha = re.search(r'\d{2}/\d{2}/\d{4}', jornada_fecha)
            etree.SubElement(match_element, "date").text = fecha.group()

        etree.SubElement(match_element, "stadium").text = estadio
        etree.SubElement(match_element, "referee").text = arbitro
        
        home_team_element = etree.SubElement(match_element, "home_team")

        etree.SubElement(home_team_element, "id").text = str(self.obtener_id(equipo_local))
        etree.SubElement(home_team_element, "name").text = equipo_local
        
        away_team_element = etree.SubElement(match_element, "away_team")
        
        etree.SubElement(away_team_element, "id").text = str(self.obtener_id(equipo_visitante))
        etree.SubElement(away_team_element, "name").text = equipo_visitante
        
        if goles_local == "sin dato":
            goles_local = 0

        if goles_visitante == "sin dato":
            goles_visitante = 0

        home_goals = int(goles_local)
        away_goals = int(goles_visitante)
        score_element = etree.SubElement(match_element, "score")
        
        if home_goals > away_goals:
            etree.SubElement(score_element, "winner").text = "home_team"
        elif home_goals < away_goals:
            etree.SubElement(score_element, "winner").text = "away_team"
        else:
            etree.SubElement(score_element, "winner").text = "draw"
        
        full_time_element = etree.SubElement(score_element, "full_time")
        etree.SubElement(full_time_element, "home_team").text = str(home_goals)
        etree.SubElement(full_time_element, "away_team").text = str(away_goals)
        
        if goleadores:
            scorers_element = etree.SubElement(match_element, "scorers");
            for goleador,minuto in goleadores:
                scorer_element = etree.SubElement(scorers_element, "scorer");
                etree.SubElement(scorer_element, "name").text = str(goleador.text)
                etree.SubElement(scorer_element, "minute").text = str(minuto)
        return match_element

    def anadir_al_fichero(self, element, file_path_out):
        element_string = etree.tostring(element, pretty_print=True, encoding='unicode')
        # Abre el archivo en modo de anexar
        with open(file_path_out, "a", encoding='utf-8') as file:
            file.write(element_string)   

    def obtener_datos_liga_campeones(self):
        #enlaces_partidos = tree.xpath('//*[@id="partits-competicio"]/tr/td[1]/a')
        with open("FootballMatches.xml", "w") as file:
            file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            file.write('<matches>\n')
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            'Accept-Language': 'es'
        }

        #self.links contiene los enlaces de las temporadas
        for link in self.links:
            page_season = requests.get("https://www.bdfutbol.com/es/" + link, headers=headers)
            tree = html.fromstring(page_season.text)

            # Selecciona todas las filas de la tabla (evitando la primera que es la cabecera)
            filas_partidos = tree.xpath('//*[@id="partits-competicio"]/tr')[1:]

            for fila in filas_partidos:
                #print(fila.xpath('./td[1]/a/@href')[0])
                #Hacemos petición a la página del partido
                page_match = requests.get("https://www.bdfutbol.com/es" + fila.xpath('./td[1]/a/@href')[0][2:], headers=headers)
                print("https://www.bdfutbol.com/es" + fila.xpath('./td[1]/a/@href')[0][2:])
                tree_match = html.fromstring(page_match.text)

                time.sleep(np.random.randint(0.5, 1))

                competicion = tree_match.xpath('/html/body/div[3]/div[2]/div[1]/div/div[1]/div[2]/a')
                if competicion:
                    competicion = competicion[0].text
                else:
                    competicion = "sin dato"

                estadio = tree_match.xpath('/html/body/div[3]/div[2]/div[1]/div/div[3]/div[2]')
                if estadio:
                    estadio = estadio[0].text
                else:
                    estadio = "sin dato"

                jornada_fecha = tree_match.xpath('/html/body/div[3]/div[2]/div[1]/div/div[4]/div[2]')
                if jornada_fecha:
                    jornada_fecha = jornada_fecha[0].text
                else:
                    jornada_fecha = "sin dato"

                arbitro = tree_match.xpath('/html/body/div[3]/div[2]/div[4]/div[2]/a/text()')
                if arbitro:  
                    arbitro = arbitro[0]
                else:
                    arbitro = "sin dato"
                
                equipo_local = tree_match.xpath('/html/body/div[3]/div[2]/div[2]/div/div[1]/span/a')
                if equipo_local:
                    equipo_local = equipo_local[0].text
                else:
                    equipo_local = "sin dato"
    
                equipo_visitante = tree_match.xpath('/html/body/div[3]/div[2]/div[2]/div/div[4]/span/a')
                if equipo_visitante:
                    equipo_visitante = equipo_visitante[0].text
                else:
                    equipo_visitante = "sin dato"
                    
                goles_local = tree_match.xpath('/html/body/div[3]/div[2]/div[2]/div/div[2]')
                if goles_local:
                    goles_local = goles_local[0].text
                else:
                    goles_local = "sin dato"

                goles_visitante = tree_match.xpath('/html/body/div[3]/div[2]/div[2]/div/div[3]')
                if goles_visitante:
                    goles_visitante = goles_visitante[0].text
                else:
                    goles_visitante = "sin dato"

                #print(competicion.text + " " + estadio.text + " " + jornada_fecha.text + " " + equipo_local.text + " VS "+ equipo_visitante.text + " " + goles_local.text + " - "+ goles_visitante.text + " " + arbitro)
                temporada = link[6:13]
                jornadasObtenidas = "sin dato"
                match = self.crear_datos_partido(competicion, jornadasObtenidas, temporada, estadio, jornada_fecha, arbitro, equipo_local, equipo_visitante, goles_local, goles_visitante)
                self.anadir_al_fichero(match, "FootballMatches.xml")
                self.linksProcesador += 1
                print("Partidos procesados: " + str(self.linksProcesador))
        
        with open("FootballMatches.xml", "a") as file:
            file.write('</matches>\n')
    
    def obtener_datos_liga(self, url, jornadas, temporada):
        with open("FootballMatches"+temporada+".xml", "w") as file:
            file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            file.write('<matches>\n')
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            'Accept-Language': 'es'
        }
        page_season = requests.get(url+"?tab=results&jornada=-", headers=headers)
        tree = html.fromstring(page_season.text)
        jornadasTotales = jornadas
        for jornadasObtenidas in range(1, jornadasTotales+1):

            #print(url+"?tab=results&jornada="+str(jornadasObtenidas))
            path = '//table[@class="taula_estil taula_estil-16"]/tr[@class="jornadai ij'+str(jornadasObtenidas)+'"]/td/a/@href'
            filas_partidos = tree.xpath(path)
            for fila in filas_partidos:
                #Hacemos petición a la página del partido
                if not fila.endswith(".html"):
                    page_match = requests.get("https://www.bdfutbol.com/es" + fila[2:], headers=headers)
                    print("https://www.bdfutbol.com/es" + fila[2:])
                    tree_match = html.fromstring(page_match.text)

                    time.sleep(np.random.randint(0.5, 1))

                    path_goles = '//div[@class="row pt-1 pt-md-3 pb-2 text-center mb-0 mb-md-4"]/div/div/div[@class="text-blanc"]/a'
                    goleadores = tree_match.xpath(path_goles)
                    
                    path_minutos = '//div[@class="row pt-1 pt-md-3 pb-2 text-center mb-0 mb-md-4"]/div/div/div[@class="text-blanc"]/text()'
                    minutos = tree_match.xpath(path_minutos)
                    
                    minutos_formateados = []
                    for minuto in minutos:
                        minuto = minuto.strip()
                        minuto = minuto.replace("'", "")
                        minuto = minuto.replace("\r\n", "")
                        minuto = minuto.split()
                        if minuto and minuto[0].isdigit():
                            minutos_formateados.append(int(minuto[0]))

                    goleadores_y_minutos = list(zip(goleadores, minutos_formateados))

                    if(len(goleadores) == 0):
                        goleadores = None

                    competicion = tree_match.xpath('/html/body/div[3]/div[2]/div[1]/div/div[1]/div[2]/a')
                    if competicion:
                        competicion = competicion[0].text
                    else:
                        competicion = "sin dato"

                    estadio = tree_match.xpath('/html/body/div[3]/div[2]/div[1]/div/div[3]/div[2]')
                    if estadio:
                        estadio = estadio[0].text
                    else:
                        estadio = "sin dato"

                    jornada_fecha = tree_match.xpath('/html/body/div[3]/div[2]/div[1]/div/div[4]/div[2]')
                    if jornada_fecha:
                        jornada_fecha = jornada_fecha[0].text
                    else:
                        jornada_fecha = "sin dato"

                    arbitro = tree_match.xpath('/html/body/div[3]/div[2]/div[4]/div[2]/a/text()')
                    if arbitro:  
                        arbitro = arbitro[0]
                    else:
                        arbitro = "sin dato"
                    
                    equipo_local = tree_match.xpath('/html/body/div[3]/div[2]/div[2]/div/div[1]/span/a')
                    if equipo_local:
                        equipo_local = equipo_local[0].text
                    else:
                        equipo_local = "sin dato"

                    equipo_visitante = tree_match.xpath('/html/body/div[3]/div[2]/div[2]/div/div[4]/span/a')
                    if equipo_visitante:
                        equipo_visitante = equipo_visitante[0].text
                    else:
                        equipo_visitante = "sin dato"
                        
                    goles_local = tree_match.xpath('/html/body/div[3]/div[2]/div[2]/div/div[2]')
                    if goles_local:
                        goles_local = goles_local[0].text
                    else:
                        goles_local = "sin dato"

                    goles_visitante = tree_match.xpath('/html/body/div[3]/div[2]/div[2]/div/div[3]')
                    if goles_visitante:
                        goles_visitante = goles_visitante[0].text
                    else:
                        goles_visitante = "sin dato"

                    #print(competicion.text + " " + estadio.text + " " + jornada_fecha.text + " " + equipo_local.text + " VS "+ equipo_visitante.text + " " + goles_local.text + " - "+ goles_visitante.text + " " + arbitro)
                    match = self.crear_datos_partido(competicion, jornadasObtenidas, temporada, estadio, jornada_fecha, arbitro, equipo_local, equipo_visitante, goles_local, goles_visitante, goleadores_y_minutos)
                    self.anadir_al_fichero(match, "FootballMatches"+temporada+".xml")
                    self.linksProcesador += 1
                    print("Partidos procesados: " + str(self.linksProcesador))
        
        with open("FootballMatches"+temporada+".xml", "a") as file:
            file.write('</matches>\n')
            
scraper = WebScraper()
#scraper.obtener_links_temporadas()
scraper.obtener_datos_liga("https://www.bdfutbol.com/es/t/t2022-23.html", 38, "2022-23")
#scraper.obtener_datos()