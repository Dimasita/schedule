# Schedule   
docker build . -t image_name  
docker run -i --rm \
                    -v `pwd`/NAME_OUTPUT_FILE.JSON:/app/output.json \  
                    -v `pwd`/NAME_INPUT_FILE.JSON:/app/input.json \  
                    -v `pwd`/benchmark.txt:/app/benchmark.txt \  
                    -e univer=UNIVER_NAME image_name  
<br>
Если есть входной файл, из него берутся все имеющиеся в нем поля из списка:   
- groups   
- teachers  
- subjects  

Если входной файл не нужен, то убрать его привязку где run.  
Обязательная переменная univer - название универа.
1. Политех = spbstu  
  Будет дополняться (наверно))
   
Пример с входным файлом:  
docker run -i --rm -v `pwd`/output.json:/app/output.json -v `pwd`/input.json:/app/input.json -v `pwd`/benchmark.txt:/app/benchmark.txt -e univer=spbstu image_name  
Без входного файла:  
docker run -i --rm -v `pwd`/output.json:/app/output.json -v `pwd`/benchmark.txt:/app/benchmark.txt -e univer=spbstu image_name  
