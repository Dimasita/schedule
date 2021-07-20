# Schedule   
## Docker
docker build path/to/schedule_folder(`.` for current) -t `image_name`  
docker run -i --rm \
                    -v \`pwd\`/`NAME_OUTPUT_FILE.JSON`:/app/output.json \  
                    -v \`pwd\`/`NAME_INPUT_FILE.JSON`:/app/input.json \  
                    -v \`pwd\`/timings.txt:/app/timings.txt \  
                    -e univer=`UNIVER_NAME` `image_name`  
<br>
## Info
Если есть входной файл, из него берутся все имеющиеся в нем поля из списка:
- groups   
- teachers  
- subjects  

Если входной файл не нужен, то убрать его привязку где run.  
Обязательная переменная univer - название универа.  

Готовые:

    1. Политех = spbstu  
    2. ЛЭТИ = etu  
    3. Военмех = bstu  

Скоро будут:

    4. СПбГЭУ = unecon  
    5. ИТМО = itmo  
    Будет дополняться (наверно))
   
## Example
Пример с входным файлом:  
docker run -i --rm -v \`pwd\`/output.json:/app/output.json -v \`pwd\`/input.json:/app/input.json -v \`pwd\`/timings.txt:/app/timings.txt -e univer=spbstu image_name  
<br>
Без входного файла:  
docker run -i --rm -v \`pwd\`/output.json:/app/output.json -v \`pwd\`/timings.txt:/app/timings.txt -e univer=spbstu image_name  