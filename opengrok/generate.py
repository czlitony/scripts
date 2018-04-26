import os
import shutil

SOURCE = 'D:\\jabber'


def update_codes(root_dir):
     for dir in os.listdir(root_dir):
        path = os.path.join(root_dir, dir)
        print '\n' + path
        if os.path.isdir(path):
            os.chdir(path)
            os.system('svn cleanup')
            os.system('svn update')
        else:
            print 'Not a directory'


def delete_old_data():
    grokdata_path = r'D:\OpenGrok\opengrok-1.0\grokdata'
    shutil.rmtree(grokdata_path, True)
    if not os.path.isdir(grokdata_path):
        os.mkdir('D:\OpenGrok\opengrok-1.0\grokdata')


def restart_tomcat():
    os.system(r'"C:\Program Files (x86)\Apache Software Foundation\Tomcat 8.0\bin\Tomcat8.exe" stop')
    os.system(r'"C:\Program Files (x86)\Apache Software Foundation\Tomcat 8.0\bin\Tomcat8.exe" start')


def generate_opengrok_data():
    # delete_old_data()

    # os.system('java -jar D:\OpenGrok\opengrok-1.0\lib\opengrok.jar -W D:\OpenGrok\OpenGrok-1.0\configuration.xml -i *.jar -c D:\Ctags\ctags58\ctags.exe -P -S -v -s ' + SOURCE + ' -d D:\OpenGrok\OpenGrok-1.0\grokdata')
    os.system('java -Xmx512m -jar D:\OpenGrok\opengrok-1.0\lib\opengrok.jar -W D:\OpenGrok\OpenGrok-1.0\configuration.xml -c D:\Ctags\ctags58\ctags.exe -P -S -v -s ' + SOURCE + ' -d D:\OpenGrok\OpenGrok-1.0\grokdata')
    restart_tomcat()


if __name__ == '__main__':
    update_codes(SOURCE)
    generate_opengrok_data()
