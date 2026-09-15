# Slovníky AI

Následující příkazy předpokládají nastavení následujících proměnných prostředí.
Ty je možné nastavit ručně, nebo načíst z .env souboru pomocí skriptu níže.
```shell
# Název Azure subscription.
$env:SUBSCRIPTION=""
# Název Azure resource group.
$env:RESOURCE_GROUP=""
# Lokalita pro tvorbu zdrojů.
$env:LOCATION=""
# Název Azure "Container registry" pro ukládání Docker images.
$env:CONTAINER_REGISTRY=""
# Název Azure "Container Apps Environment", tedy prostředí pro hostování
# naších aplikací.
$env:CONTAINER_APP=""
# Název Azure "Managed Identity" pro zajištění přístupu z
# "Container Apps Environment" do "Container registry".
# Aktuálně není využité.
$env:IDENTITY=""
# Název Azure "Container App" vytvořené v "Container Apps Environment".
$env:APP=""
# Název Azure "Log Analytics workspace" pro uložení a zpracování logů
# z "Container Apps Environment". Pokud nedáme vlastní Azure vytvoří nový.
$env:LOG=""
# Název Azure "Storage account" pro uložení dat.
$env:STORAGE=""
# Název Azure "File shares" v "Storage account".
# Jedná se o sdílené datové úložiště.
$env:STORAGE_SHARE=""
# Název Azure "File share name", poskytující přístup k "File shares"
# pro "Container App".
$env:STORAGE_MOUNT=""
```

Výchozí hodnoty jako .env soubor použité pro testovací nasazení:
```shell
SUBSCRIPTION="..."
RESOURCE_GROUP="..."
#
LOCATION="northeurope"
CONTAINER_REGISTRY="ismddockerregistry"
CONTAINER_APP="ismd-container-apps"
IDENTITY="ismd-identity"
APP="semantic-modeling-assistant"
LOG="ismd-log-workspace"
STORAGE="ismdstorage"
STORAGE_SHARE="ismd-storage-share"
STORAGE_MOUNT="ismd-storage-share-mount"
```

```shell
# Načte obsah ze souboru ./azure-container-app/.env do proměnných prostředí.
Get-Content ./azure-container-app/.env | foreach {
  $name, $value = $_.split('=')
  if ([string]::IsNullOrWhiteSpace($name) -or $name.StartsWith('#')) {
    return
  }
  Set-Content env:\$name $value
}
```

## Nastavení az

```shell
# Přihlásíme se do Azure, je třeba vybrat správnou "subscription".
az login
# "subscription" je možné změnit pomocí následujícího příkazu.
az account set --subscription $env:SUBSCRIPTION
```

## Příprava container registry

```shell
# Založení Azure Container Registry (ACR).
az acr create --resource-group $env:RESOURCE_GROUP --name $env:CONTAINER_REGISTRY --sku Basic
# Povolení admin přístupu.
az acr update --resource-group $env:RESOURCE_GROUP --name $env:CONTAINER_REGISTRY --admin-enabled true
# Povolení přístupu k ACR skrze ARM token.
az acr config authentication-as-arm show --registry $env:CONTAINER_REGISTRY
```

## Příprava identity pro přístup

```shell
az identity create --resource-group $env:RESOURCE_GROUP --name $env:IDENTITY
# Získání identifikátoru identity a uložení do IDENTITY_ID.
$env:IDENTITY_ID=(az identity show --resource-group $env:RESOURCE_GROUP --name $env:IDENTITY --query id)
```

V Azure portálu je nutné přidat přístup skrze bezpečnostní token.
Ten lze vygenerovat pro "Container registry" > "Repository permissions" > "Tokens"
Hodnoty je třeba uložit do
```shell
$env:CONTAINER_REGISTRY_LOGIN=
$env:CONTAINER_REGISTRY_PASSWORD=
```

## Sestavení a publikace Docker image

Původní kořenový `Dockerfile` skládal starý frontend a backend do jednoho image
(`semantic-modeling-assistant-frontend` + `semantic-modeling-assistant-backend`).
Tyto adresáře v repozitáři už nejsou.

Aktuální lokální běh (mock UI + agentic backend) je `docker compose` z kořene
repozitáře, viz [`DOCKER.md`](../DOCKER.md):

```shell
docker compose up --build
```

Nasazení do Azure Container Apps z tohoto starého jedno-image postupu zatím
není aktualizované.

## Příprava Azure Storage

```shell
# Vytvoření storage.
az storage account create --resource-group $env:RESOURCE_GROUP --name $env:STORAGE --location $env:LOCATION --kind StorageV2 --sku Standard_LRS  --enable-large-file-share
# Vytvoření souboru ke sdílení, 16GB.
az storage share-rm create --resource-group $env:RESOURCE_GROUP --storage-account $env:STORAGE --name $env:STORAGE_SHARE --quota 16 --enabled-protocols SMB
# Uložení klíče.
$env:STORAGE_KEY=(az storage account keys list -n $env:STORAGE --query "[0].value")
```

## Příprava Container apps

```shell
# Vytvoříme si vlastní Log Analytics workspace.
# Toto není nutné, vytvořil by se v dalším kroku, ale takto mu můžeme dát jméno.
az monitor log-analytics workspace create --resource-group $env:RESOURCE_GROUP --workspace-name $env:LOG
# Získáme identifikátor pro customerId nikoliv id.
# https://github.com/Azure/azure-cli/issues/27098#issuecomment-1683029636
$env:LOG_ID=(az monitor log-analytics workspace show --resource-group $env:RESOURCE_GROUP --workspace-name $env:LOG --query customerId -o tsv)
# Získáme klíč.
$env:LOG_KEY=(az monitor log-analytics workspace get-shared-keys --resource-group $env:RESOURCE_GROUP --workspace-name $env:LOG --query primarySharedKey -o tsv)
```

```shell
# Vytvoření obálky pro aplikace
az containerapp env create --name $env:CONTAINER_APP --resource-group $env:RESOURCE_GROUP --location $env:LOCATION --logs-workspace-id $env:LOG_ID --logs-workspace-key $env:LOG_KEY
```

```shell
# Vytvoření přístupu do storage, ten se tvoří pro obálku aplikace.
az containerapp env storage set --access-mode ReadWrite --azure-file-account-name $env:STORAGE --azure-file-account-key $env:STORAGE_KEY --azure-file-share-name $env:STORAGE_SHARE --storage-name $env:STORAGE_MOUNT --name $env:CONTAINER_APP --resource-group $env:RESOURCE_GROUP
```

Po úspěšném spuštění bychom měli najít záznam v "container apps environment | $env:CONTAINER_APP", Settings, Azure Files.
Bohužel kontejner nelze rovnou vytvořit s mountem, ale je třeba ho přidat později.

## Nasazení aplikace

```shell
az containerapp create --name $env:APP --resource-group $env:RESOURCE_GROUP --environment $env:CONTAINER_APP --image "$env:CONTAINER_REGISTRY.azurecr.io/semantic-modeling-assistant:latest" --target-port 80 --ingress external --registry-server "$env:CONTAINER_REGISTRY.azurecr.io" --registry-username $env:CONTAINER_REGISTRY_LOGIN --registry-password $env:CONTAINER_REGISTRY_PASSWORD
```

URL aplikace je možné najít v detailu aplikace na portálu Azure.
Následně je třeba upravit konfiguraci z hlediska dat a konfigurace přístupů.

Začneme vytvořením tajemství: Container App > Security > Secrets
- openapi-key
- user-keys
Vložíme hodnoty z .env souboru.

Následně je třeba tyto vložit do proměnných prostředí : Container App > Application > Containers
- OPENAI_API_KEY
- USER_KEYS

Dále je třeba připojit datové úložiště prostor.
Nejlépe skrze: Container App > Application > Containers > Volume mounts.
Tam je možné volume vytvořit a rovnou připojit.

## Konfigurace škálování

Z ekonomického hlediska je ideálně povolit nasazení 0 replik.
Pokud aplikace není po nastavený čas používána, tak se počet nasazení sníží na 0.
Toto nastavení je možné provést: Container App > Application > Scale.

Nevýhodou škálování na 0 je nutnost aplikaci nastartovat v případě potřeby.
V době psaní to trvá zhruba minutu.
Tento čas by možná bylo možné zlepšit zmenšením Docker image a zrychlením, jeho spuštění.

## Odkazy

- [Quickstart: Deploy your first container app with containerapp up](https://learn.microsoft.com/en-us/azure/container-apps/get-started)
- [Tutorial: Build and deploy your app to Azure Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/tutorial-code-to-cloud)
- [Use storage mounts in Azure Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/storage-mounts?tabs=smb&pivots=azure-cli#azure-files)
- [Tutorial: Create an Azure Files volume mount in Azure Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/storage-mounts-azure-files)
- [Use storage mounts in Azure Container Apps](https://docs.azure.cn/en-us/container-apps/storage-mounts)
- [Tutorial: Build and deploy from source code to Azure Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/tutorial-deploy-from-code)
- [Azure Container Apps ARM and YAML template specifications](https://learn.microsoft.com/en-us/azure/container-apps/azure-resource-manager-api-spec?tabs=yaml)
