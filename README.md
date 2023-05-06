# scraping-tmdb
Web scraping en tmdb para crear fixtures para mi repositorio django-api-example (https://github.com/AdrSanWal/django-api-example).

Existe una API en tmdb (https://www.themoviedb.org/documentation/api?language=es), pero
mi intención es obtener unos cuantos datos de muestra para poder modificarlos.

Aunque no se utiliza su api, si se recogen sus datos, por lo que si vas a hacer uso de ellos, lee antes sus
terminos de uso: https://www.themoviedb.org/documentation/api/terms-of-use.

Este scraping vuelca los datos obtenidos en data.json, que actualmente contiene las paginas de peliculas de la 1 a la 5
(en torno a 1000 fixtures. Para obtener más datos modificar start_page y end_page del script.

Por ahora selenium no está preparado para trabajar en segundo plano
