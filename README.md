# Smart Journey Flow 

Micro serviço responsável por tratar funções relativas ao fluxo do SmartJourney

## Testes e Cobertura de Testes
Dependencias:
* `pytest==5.4.3`
* `pytest-cov==2.10.0`

Executar o comando: 
```sh
$ py.test tests/ --cov=flow --cov-report html --cov-report term
```

Executar Nameko localmente:
```sh
$ nameko run --config flow/config.yaml flow.rpc
```

Executar Docker localmente:
```sh
$ docker-compose -f docker-compose.yml up --build
```