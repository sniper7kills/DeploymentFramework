from core.models.Module import Module
from plugins.RemoteOffice.Template import Template as BasePlugin
from core.models.Settings import Settings

from . import functions as Functions

class Plugin(BasePlugin):

    listenForEvents = {
        'RO.mariadb.createDatabase': 'createDatabase',
    }

    availableCommands = {
        'RO.mariadb.createDatabase': 'Create a new Database'
    }

    # The RO Base is 0; We need to be above that...
    priority = 10

    # Prompts User for Configuration Options
    def preformOfficePrompts(self):
        questions = [
            # REF: https://github.com/CITGuru/PyInquirer/
            {
                'type': 'password',
                'name': 'root_password',
                'message': '[%s] New ROOT user password:' % str.upper(self.getName())
            },
            {
                'type': 'input',
                'name': 'default_database',
                'message': '[%s] New MYSQL database name:' % str.upper(self.getName()),
                'default': 'itsupport'
            },
            {
                'type': 'input',
                'name': 'default_user',
                'message': '[%s] New MYSQL user name:' % str.upper(self.getName()),
                'default': 'itsupport'
            },
            {
                'type': 'password',
                'name': 'default_password',
                'message': '[%s] New MYSQL user\'s password:' % str.upper(self.getName())
            },

        ]
        
        questionsToAsk = []
        for question in questions:
            if self.promptRequired(question['name']):
                questionsToAsk.append(question)

        self.preformPrompts(questionsToAsk)

    # Used to create any storage and initizalation directories needed
    def createFolderStructure(self, install_dir = './office'):
        # The paths the plugin needs to ensure exist
        paths = [
            'init/mariadb',
            'storage/mariadb/data'
        ]
        self.createFolders(paths, install_dir)

    # Used to append the plugin's docker service if it exists.
    def appendDockerService(self, docker_compose_file = 'docker-compose.yml', install_dir = './office'):
        contents = Functions.dockerFile()
        self.appendContentsToFile(contents, docker_compose_file, install_dir)


    # Used to initialize any any configuration settings that need to be deployed
    def createInitialConfig(self, install_dir = './office'):
        # ENV File
        contents = Functions.envFile(self.getSetting('root_password'), self.getSetting('default_database'), self.getSetting('default_user'), self.getSetting('default_password'))
        self.writeContentsToFile(contents, 'envs/mariadb.env', install_dir)
        


    
    # Preform any additional config before the container is launched.
    # This is useful if you need to preform API calls to finalize the config
    #   for this plugin; but need to wait for another plugin to launch first
    def preLaunchConfig(self, install_dir = './office'):
        pass

    # Preform the actual launching of docker container for this plugin
    def launchDockerService(self):
        self.events.emit("RO.launch", "mariadb")
        pass

    # Preform any post launch for this container.
    # Ensure API's are up
    # Change default passwords, Etc...
    def postLaunchConfig(self, install_dir = './office'):
        if self.promptRequired('post-launch'):
            Settings.create(plugin = self.module, key = 'post-launch', value='True')

    def createDatabase(self, db_name, db_user, db_password):
        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        install_dir = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'install_dir').get().value
        content = Functions.dbsql(db_name, db_user, db_password)

        # See if the postLaunchConfig has been run...
        if self.promptRequired('post-launch'):
            # It hasn't been run yet...
            self.writeContentsToFile(content, 'init/mariadb/%s.sql' % db_name, install_dir)
        else:
            print("TODO: preform docker ommand to create the database...")