# HelpDesk
## A SlackBot Framework
### Configuration
- **_./configs/helpdesk.cfg_** should have the following structure 

```
[DEFAULT]
token = super-secret-token
sleep_interval = 1
debug = false

[DIRECTORIES]
logs = logs
configs = configs
commands = commands

[LOGGING]
log_dir = logs
log_name = %(log_dir)s/helpdesk.log
log_level = DEBUG
```

### HelpDesk
- iterates over **_./commands_** and imports python modules, with the exception of `__init__.py`  
- when dispatching a thread to run a `ServiceProvider` command, `HelpDesk` calls `.run()` on the `ServiceProvider`
- handles the `help` command 
- when asked to run a command that is registered as a `ServiceProvider`, it will pass the following keyword-arguments

    | kwarg  | type  | description  |
    |---|---|---|
    | args  | list of strings  | arguments passed from slack to the bot  |
    | client  | slackclient.SlackClient  | HelpDesk's websocket connection to slack's RTM  |
    | config  | configparser.ConfigParser  | the configuration file used to start HelpDesk  |
    | debug  | bool  | whether debugging is on or not, useful for logging  |
    | event  | dict  | the raw message event that triggered HelpDesk's initial response |
    
- `ServiceProvider` commands are run in non-blocking threads
- when sent a **SIGHUP**, will reload all `ServiceProvider`'s source code from **_./commands_**, it will also reload **_./configs/helpdesk.cfg_**


### ServiceProviders 
- name of the `ServiceProvider` should be the name of the file dropped into **_./commands_**
- the name of the file dropped into **_./commands_** should be lowercase, because reasons
- should inherit from `ABCs.ServiceProvider.ServiceProviderABC`
- help for the `ServiceProvider` should utilize the **\_\_doc\_\_** attribute for each `ServiceProvider`
- exposes `send_message(message, channel)` a wrapper for `slackclient.api_call('chat.postMessage')`   
- exposes `run` function that has no implementation, override this to specify your ServiceProvider's behavior

