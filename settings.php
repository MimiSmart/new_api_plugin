<?php

date_default_timezone_set('Europe/Kiev');

define("LANG", "en");//select language

//begin shs settings ##################################
define("HOST", "127.0.0.1");
define("PORT", 55559);
define("SECRET_KEY","");
//end shs settings ####################################

define("BASE_DIR", dirname(__FILE__) . "/");
define("PARENT_BASE_DIR", str_replace(strrchr(substr(BASE_DIR,0,-1),"/"),"",BASE_DIR));
define("HTML_DIR", BASE_DIR . "");
define("CONF_PATH", "/home/sh2/");// /home/sh2/
define("MIMISMART_PATH", "/home/sh2/");// /home/sh2/
define("HOME_PATH", "/home/");// /home/
define("STORAGE_PATH", "/storage/");

define("PATH_TO_XML_FILE", CONF_PATH . "logic.xml");
define("PATH_TO_SCRIPTS", CONF_PATH . "scripts");
define("CLASSES_DIR", HTML_DIR . "classes/");
define("CONTROLLERS", HTML_DIR . "data/controller/");
define("LOGS_DIR", BASE_DIR . "logs/");//set chmod 777
define("BACKUP_DIR", STORAGE_PATH . "backup/");
define("SETUP_DIR", HOME_PATH . "system/");
define("TMP_PATH", BASE_DIR . "tmp/");
define("PHP_ERROR_LOG", LOGS_DIR . "errors.txt");
define("SH_CLIENT_LOG", LOGS_DIR . "shclient.txt");
define("CAMERA_PROFILES_DIR", CONF_PATH . "cam_profiles/");
define("RC_PROFILES_DIR", CONF_PATH . "pult_profiles/");
define("KEYS_FILE", CONF_PATH . "keys.txt");
define("SETTINGS_DIR", HOME_PATH . "settings/");
define("CACHE_DIR", BASE_DIR . "cache/");
define("LOCALE_DIR", BASE_DIR . "resources/scripts/locale/");
define("TRANSLATE_FILE", BASE_DIR . "resources/scripts/tr.xml");
define("PATH_TO_GSM_MENU", BASE_DIR . "gsmmenu/");
define("PATH_TO_GSM_MENU_XML_FILE", PATH_TO_GSM_MENU . "menus.xml");
define("PATH_TO_GSM_MENU_DEF_AUDIO_FILES", PATH_TO_GSM_MENU . "default_audio_files");
define("PATH_TO_GSM_MENU_FILES", PATH_TO_GSM_MENU . "menu_files");
define("URL_GET_FILE_FROM_TEXT", "http://s2.smarthouse.ua:8080/say_wav.php?text=");
define("URL_GET_DEVICE_STATUS_FILE", "GET:http://192.168.1.125/gsmwav/getwav.php");
define("LOGICXML_BACKUP_DIR", LOGS_DIR . "backup/");
define("VIEWER_STYLES_DIR", BASE_DIR . "resources/scripts/highlight.js/styles");
define("ACE_THEMES_DIR", BASE_DIR . "resources/scripts/ace");
define("WEB_DIR", HOME_PATH . "web/");
define("TMP_DIR", HOME_PATH . "tmp");
define("RF_LOGS_DIR", WEB_DIR . "rflogs");

define("CMD_SCRIPTS_DIR", WEB_DIR . "cmdScripts/");//set chmod 777
define("DEVSTATE_ALIVE_TIME", 1800);
define("DEVICES_STATE", CMD_SCRIPTS_DIR . "devsState.txt");
define("DEVSTATE_SCRIPT", CMD_SCRIPTS_DIR . "getDevsState.php >/dev/null &");
define("DEVSTATE_SCRIPT_LOCK", CMD_SCRIPTS_DIR . "getDevsState.lock");
define("DEVSTATE_SCRIPT_LOG", CMD_SCRIPTS_DIR . "getDevsStateLog.txt");
define("DEVSTATE_EVENTS_LOG", CMD_SCRIPTS_DIR . "eventsLog.txt");
define("DEVICES_LOG_ON", FALSE);

define("SEMKEYS_FOLDER", "/home/mimismartServer/sem_keys/");//semaphores folder
define("SEMKEYS_PROJECT", "s");
define("SHMEM_KEY", SEMKEYS_FOLDER . "shm.txt");
define("SHMEM_SIZE", 20480);//shared memory size



define("SHARED_ATTRS_DIR", WEB_DIR . "sharedAttrs/");//set chmod 777
define("SHARED_ATTRS_FILE", SHARED_ATTRS_DIR . "attrs.xml");

define("PASSWD_DIR", WEB_DIR . "p/");//set chmod 777
define("PASSWD_FILE", PASSWD_DIR . ".passwd.txt");
define("PASSWD_FIELD", "panel_password");

//for production server
define("SERVER_LOG", CONF_PATH . "logs/log.txt");
define("SERVER_LOG_DEVICE", CONF_PATH . "logs/log-devices.txt");
define("SERVER_CONFIG", CONF_PATH . "config.sh");
define("SERVER_LOGIC_FOLDER", CONF_PATH . "logic");

define("SETTINGS_CONF_FILE", HOME_PATH . "settings/config.txt");// /home/config
define("GET_STAT_COMMAND", "sudo " . SETUP_DIR . "stat.sh");//sudo /home/setup/stat.sh
define("SET_IP_COMMAND", "sudo " . SETUP_DIR . "netconf.sh");//sudo /home/setup/netconf.sh
define("PATH_TO_BACKUP_SCRIPT", SETUP_DIR . "backup.sh");
define("PATH_TO_UPDATE_SCRIPT", SETUP_DIR . "update.sh");
define("PATH_TO_FIRMWARE_UPDATER", CONF_PATH . "update/updater");


define('PANEL_SECRET_KEY', 'L*E7dot@Vw%DFC?54ED');//part of authorization cookie id
define("PANEL_AUTH_COOKIE_NAME", "mimisetup-auth-id");//name of authorization cookie
define("PANEL_LANG_COOKIE_NAME", "mimisetup-lang");
define("PANEL_VIEWER_STYLE_COOKIE_NAME", "mimisetup-viewer-style");

$global_conf = array();

$global_conf["backup"] = array();
$global_conf["backup"]["manual"] = BACKUP_DIR . "manual";
$global_conf["backup"]["daily"] = BACKUP_DIR . "daily";
$global_conf["backup"]["weekly"] = BACKUP_DIR . "weekly";
$global_conf["backup"]["monthly"] = BACKUP_DIR . "monthly";

$global_conf["app"] = array();
$global_conf["app"]["shs"] = "Server software statistics";
$global_conf["app"]["shi2.zip"] = "Interface";
$global_conf["app"]["scripts"] = "Scripts database";
$global_conf["app"]["cam_profiles"] = "Cameras database";
$global_conf["app"]["mimisetup"] = "Configuration panel MimiSetup";
$global_conf["app"]["setup"] = "Systems scripts";
$global_conf["app"]["gsmwave"] = "Addons for GSM module";
$global_conf["app"]["mimicharts"] = "Charts";
$global_conf["app"]["php_api"] = "API for accessing the system";
$global_conf["app"]["webpanel"] = "Panel for access to the system";


$global_conf["modules"] = array();
$global_conf["modules"][] = array("name"=>"confPanel", "show"=>true);//server configuration
$global_conf["modules"][] = array("name"=>"scrEdGrid", "show"=>true);//scripts editor
$global_conf["modules"][] = array("name"=>"scriptsCompiledTabPanel", "show"=>true);//compiled scripts
$global_conf["modules"][] = array("name"=>"shsLog", "show"=>true);//server log
$global_conf["modules"][] = array("name"=>"shsErrorsLog", "show"=>false);//devices errors
$global_conf["modules"][] = array("name"=>"settingsForm", "show"=>true);//settings
$global_conf["modules"][] = array("name"=>"keysGrid", "show"=>true);//keys editor
$global_conf["modules"][] = array("name"=>"xmlEditor", "show"=>true);//xml editor
$global_conf["modules"][] = array("name"=>"updaterPanel", "show"=>true);//updates
$global_conf["modules"][] = array("name"=>"gsmMenuPanel", "show"=>true);//gsm menu
$global_conf["modules"][] = array("name"=>"devicesChartsPanel", "show"=>true);//devices charts
$global_conf["modules"][] = array("name"=>"devsControlPanel", "show"=>false);//control devices
$global_conf["modules"][] = array("name"=>"sharedAttrsEditor", "show"=>true);//edit shared attributes


$globalSettings = array();
$globalSettings["shs"] = array("");
$globalSettings["shs"]["host"] = HOST;
$globalSettings["shs"]["port"] = PORT;
$globalSettings["shs"]["secret_key"] = SECRET_KEY;
$globalSettings["shs"]["logFile"] = SH_CLIENT_LOG;

$globalSettings["semKeysFolder"] = SEMKEYS_FOLDER;
$globalSettings["semKeysProject"] = SEMKEYS_PROJECT;
$globalSettings["shmKey"] = SHMEM_KEY;
$globalSettings["shmSize"] = SHMEM_SIZE;
$globalSettings["debug"] = FALSE;
$globalSettings["logFile"] = PHP_ERROR_LOG;
$globalSettings["shmemVars"] = array();
$globalSettings["shmemVars"]["shevents"] = "shevents";

$globalSettings["serverQueue"] = SEMKEYS_FOLDER . "server.msgqueue.txt";
$globalSettings["homebridgeConf"] = HOME_PATH . "homebridge/config/config.json";

$globalSettings["glbConf"] = $global_conf;
$globalSettings["logicXmlFile"] = PATH_TO_XML_FILE;
$globalSettings["downloadFWLink"] = "https://s2.smarthouse.ua/firmware/index.php";
$globalSettings["downloadFWAuth"] = array(
    "login"=>"viktor",
    "password" => "583775"
);

$globalSettings["moduleType"] = array(
    "0"=>array("sysname"=>"CM9","name"=>"CM9", "range"=>"500-600","upm"=>"1"),
    "13"=>array("sysname"=>"RS232/485","name"=>"RS232/485","upm"=>"1"),
    "15"=>array("sysname"=>"GW","name"=>"GW","upm"=>"1"),
    "17"=>array("sysname"=>"HCX8","name"=>"HCX8","upm"=>"1"),
    "30"=>array("sysname"=>"Micro2","name"=>"Micro2","upm"=>"2"),
    "31"=>array("sysname"=>"DALI","name"=>"DALI","upm"=>"2"),
    "35"=>array("sysname"=>"Micro","name"=>"Micro","upm"=>"2"),
    "48"=>array("sysname"=>"GW5","name"=>"GW5","upm"=>"2"),
    "58"=>array("sysname"=>"CAN-M","name"=>"CAN-M","upm"=>"2"),
    "77"=>array("sysname"=>"DM04","name"=>"DM04","upm"=>"2"),
    "78"=>array("sysname"=>"CAN-MLI","name"=>"CAN-MLI","upm"=>"2")
);

$globalSettings["fwUpdater2"] = "/home/system/updater.sh";
$globalSettings["modulesDocsPath"] = BASE_DIR . "modulesDocs/";

$globalSettings["appUpdater"] = "/home/system/appUpdater.sh";
$globalSettings["apps"] = array();
$globalSettings["apps"][1] = array("name"=>"MimiSetup","install"=>"mimi-mimisetup-rpi3+");
$globalSettings["apps"][2] = array("name"=>"MimiServer","install"=>"mimi-srv");
$globalSettings["apps"][3] = array("name"=>"Siri","install"=>"mimi-siri");

?>