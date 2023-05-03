import json
from os import path

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


URL_BASE = 'https://www.themoviedb.org'


class Fixture():
    def __init__(self, model):
        self.model = f'core.{model}'
        self.fields = {}

    def get_id(self, unique_field, path=None):
        with open('data.json', 'r+') as file:
            self.pk = 0
            fixtures = json.load(file)
            model_fixtures = [_ for _ in fixtures if _['model'] == self.model]
            # check if is already a fixture in data.json
            for model in model_fixtures:
                if model['pk'] >= self.pk:
                    self.pk = model['pk'] + 1
                # if its a film fixture, it needs 'title', if its a person
                # fixture it need 'name'
                search_field = {'core.person': 'name',
                                'core.film': 'title',
                                'core.category': 'name'}
                if model['fields'][search_field[self.model]] == unique_field:
                    return model['pk']
            # if is not in data.json, save it
            # person
            file.seek(0)
            if self.model == 'core.person':
                scraper = ScrapingPerson(path)
                self.fields = scraper.get_info()
            elif self.model == 'core.category':
                self.fields = {"name": unique_field, "description": None}
            elif self.model == 'core.film':
                scraper = ScrapingFilm(path)
                self.fields = scraper.get_info()
                # As people and categories have been introduced, you have to reload it
                fixtures = json.load(file)
            file.seek(0)
            new_fixture = {"pk": self.pk, "model": self.model, "fields": self.fields}
            fixtures.append(new_fixture)
            json.dump(fixtures, file, indent=2)
            return self.pk


class Scraping():
    options = Options()
    # # Open silently
    # options.add_argument("--headless")
    # # Prevent browser to close automatically
    # options.add_experimental_option('detach', True)

    def __init__(self, path, class_name):
        self.url = URL_BASE + path
        self.driver = webdriver.Chrome(options=self.options)
        # self.driver = webdriver.Firefox()
        self.class_name = class_name

    def get_page(self):
        """
        Wait for the page to load, and accept the preferences. Wait again
        for items to load
        """
        self.driver.get(self.url)
        wait = WebDriverWait(self.driver, 10)

        element = wait.until(EC.element_to_be_clickable((By.ID, "onetrust-reject-all-handler")))
        element.send_keys(Keys.RETURN)

        wait.until(EC.presence_of_element_located((By.CLASS_NAME, self.class_name)))


class ScrapingPerson(Scraping):
    right_info = '//div[@class="title"]'
    biography_xpath = '//div[contains(@class, "text") and contains(@class, "initial")]'
    left_info_xpath = '//div[contains(@class, "grey_column")]'
    photo_xpath = '//div[@class="image_content"]/img'
    facts_xpath = '//div/section/section'

    def __init__(self, path):
        self.model = 'person'
        self.age = None
        super().__init__(f'/person/{path}', class_name="content_wrapper")

    def _prepare_info(self, webelement, xpath, particular=None):
        if particular:
            xpath = f'{xpath}/p/strong[bdi="{particular}"]/..'
        try:
            webelem = webelement.find_element(By.XPATH, xpath)
        except NoSuchElementException:
            return None
        if xpath == self.photo_xpath:
            return webelem.get_attribute("src")
        info = webelem.text
        if particular:
            title, info = info.split('\n')
            if info == '-':
                return None
            if title == "Fecha de defunción":
                info, age, _ = info.replace('(', '').split(' ')
                self.age = int(age)
            if title == "Fecha de nacimiento":
                if self.death_date:
                    info = info.strip()
                else:
                    info, age, _ = info.replace('(', '').split(' ')
                    self.age = int(age)
            if title == "Sexo":
                genders = {"Masculino": "M", "Femenino": "F"}
                info = genders[info]
        return info

    def get_info(self):
        self.get_page()
        right_info = self.driver.find_element(By.XPATH, self.right_info)
        self.name = right_info.find_element(By.TAG_NAME, 'a').text
        self.biography = self._prepare_info(right_info, self.biography_xpath)
        left_info = self.driver.find_element(By.XPATH, self.left_info_xpath)
        self.photo = self._prepare_info(left_info, self.photo_xpath)
        self.gender = self._prepare_info(left_info,
                                         self.facts_xpath,
                                         particular='Sexo')
        self.principal_role = self._prepare_info(left_info,
                                                 self.facts_xpath,
                                                 particular='Conocido por')
        self.death_date = self._prepare_info(left_info,
                                             self.facts_xpath,
                                             particular='Fecha de defunción')
        self.birth_date = self._prepare_info(left_info,
                                             self.facts_xpath,
                                             particular='Fecha de nacimiento')
        self.birth_place = self._prepare_info(left_info,
                                              self.facts_xpath,
                                              particular='Lugar de nacimiento')
        return {
            "name": self.name,
            "photo": self.photo,
            "gender": self.gender,
            "principal_role": self.principal_role,
            "birth_date": self.birth_date,
            "death_date": self.death_date,
            "age": self.age,
            "birth_place": self.birth_place,
            "biography": self.biography
        }


class ScrapingFilm(Scraping):
    poster_xpath = '//section[contains(@class,"poster")]'
    title_xpath = '//div[contains(@class,"title")]'
    facts_xpath = '//div[@class="facts"]'
    certification_xpath = '//span[@class="certification"]'
    genres_xpath = '//span[@class="genres"]'
    duration_xpath = '//span[@class="runtime"]'
    score_xpath = '//div[@class="percent"]/span'
    overview_xpath = '//div[@class="overview"]/p'
    people_xpath = '//ol[contains(@class,"people")]/li'
    bottom_xpath = '//div[@class="content_wrapper"]'
    right_xpath = '//section[contains(@class, "facts")]'

    def __init__(self, path):
        self.model = 'film'
        self.characters = []
        self.director = []
        self.screenplay = []
        self.story = []
        self.novel = []
        self.writer = []
        self.cast = []

        super().__init__(f'/movie/{path}', class_name="single_column")

    def _prepare_info(self, webelement, xpath, particular=None):
        if xpath == self.people_xpath:
            roles_fields = {
                'Characters': self.characters,
                'Director': self.director,
                'Screenplay': self.screenplay,
                'Story': self.story,
                'Novel': self.novel,
                'Writer': self.writer
            }
            people = webelement.find_elements(By.XPATH, xpath)

            for person in people:
                if 'filler' in person.get_attribute("class"):
                    break
                name, roles = person.text.split('\n')
                url_person = person.find_element(By.LINK_TEXT, name).get_attribute("href")
                last_path = path.basename(path.normpath(url_person))
                f = Fixture('person')
                person_id = f.get_id(name, last_path)
                if person.get_attribute("class") == 'card':
                    self.cast.append(person_id)
                elif person.get_attribute("class") == 'profile':
                    list_roles = roles.split(', ')
                    for role in list_roles:
                        roles_fields[role].append(person_id)

        if xpath == self.score_xpath:
            text = webelement.find_element(By.XPATH, xpath).get_attribute("class")
            text = text.split('-r')[1]
            if text.isdigit():
                return f'{text}%'
            return 'NR'

        if xpath == self.right_xpath:
            xpath1 = f'{xpath}/p/strong[text()="{particular}"]/..'
            xpath2 = f'{xpath}/p/strong[bdi="{particular}"]/..'
            xpath = f'{xpath1} | {xpath2}'
            try:
                info = webelement.find_element(By.XPATH, xpath).text
            except NoSuchElementException:
                # If it does not exist, it is because the title was not translated
                if particular == 'Título original':
                    return self.title
                return None
            title, info = info.split('\n')
            if info == '-':
                return None
            return info

        info = webelement.find_element(By.XPATH, xpath).text

        if xpath == '//h2/span':  # year
            info = info.replace('(', '').replace(')', '-01-01')

        if xpath == self.genres_xpath:  # categories (genres)
            categories_ids = []
            categories = info.split(', ')
            for category in categories:
                f = Fixture('category')
                categories_ids.append(f.get_id(category))
            info = categories_ids

        return info

    def get_info(self):
        self.get_page()
        poster = self.driver.find_element(By.XPATH, self.poster_xpath)
        self.image = poster.find_element(By.TAG_NAME, 'img').get_attribute('src')
        title = poster.find_element(By.XPATH, self.title_xpath)
        self.title = title.find_element(By.XPATH, '//h2/a').text
        self.year = self._prepare_info(title, '//h2/span')
        facts = title.find_element(By.XPATH, self.facts_xpath)
        self.certification = facts.find_element(By.XPATH, self.certification_xpath).text
        self.category = self._prepare_info(facts, self.genres_xpath)
        self.duration = facts.find_element(By.XPATH, self.duration_xpath).text
        self.score = self._prepare_info(poster, self.score_xpath)
        self.overview = poster.find_element(By.XPATH, self.overview_xpath).text
        self._prepare_info(poster, self.people_xpath)
        bottom_info = self.driver.find_element(By.XPATH, self.bottom_xpath)
        self.original_title = self._prepare_info(bottom_info,
                                                 self.right_xpath,
                                                 particular='Título original')
        self.state = self._prepare_info(bottom_info,
                                        self.right_xpath,
                                        particular='Estado')
        self.original_language = self._prepare_info(bottom_info,
                                                    self.right_xpath,
                                                    particular='Idioma original')
        self.budget = self._prepare_info(bottom_info,
                                         self.right_xpath,
                                         particular='Presupuesto')
        self.income = self._prepare_info(bottom_info,
                                         self.right_xpath,
                                         particular='Ingresos')
        return {
            "title": self.title,
            "original_title": self.original_title,
            "state": self.state,
            "original_language": self.original_language,
            "budget": self.budget,
            "income": self.income,
            "year": self.year,
            "image": self.image,
            "certification": self.certification,
            "overview": self.overview,
            "category": self.category,
            "duration": self.duration,
            "score": self.score,
            "director": self.director,
            "characters": self.characters,
            "screenplay": self. screenplay,
            "story": self.story,
            "novel": self.novel,
            "writer": self.writer,
            "cast": self.cast
        }

if __name__ == '__main__':
    xpath = '//div[contains(@class, "card")]//a[@class="image"]'
    for n in range(1, 5):
        scrap_url = f'/movie?page={n}'
        s = Scraping(scrap_url, 'page_wrapper')
        s.get_page()
        img_tag = s.driver.find_elements(By.XPATH, xpath)
        for movie in img_tag:
            url_movie = movie.get_attribute("href").split('/')[-1]
            name_movie = movie.get_attribute('title')
            print(name_movie)
            f = Fixture('film')
            f.get_id(name_movie, url_movie)
