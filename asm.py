#!/usr/bin/python

import sys, re

inFile = sys.argv[1]
outFile = inFile.split(".")[0] + ".mif"

foIn = open(inFile, "r")
foOut = open(outFile, "w")

mifHeader = """WIDTH=32;
DEPTH=2048;
ADDRESS_RADIX=HEX;
DATA_RADIX=HEX;
CONTENT BEGIN
"""

foOut.write(mifHeader)

pragmaRegex = re.compile('^\s*\.(?P<pragma>[a-z]+)\s+(?P<name>[\w\-]+)(\s*=\s*(?P<value>[\w\-]+))?(\s*(?P<comment>;.+))?(?:\s*(\r|\n))$', re.I) #done
instRegex = re.compile('^\s*(?P<all>(?P<inst>[a-z]+)(\s+((?P<reg1>([a-z][a-z0-9][0-9]?|zero|pcs|iha|ira|idn|ssp))|((?P<imma>[\w\-]+)\((?P<reg2a>([a-z][a-z0-9][0-9]?|zero|pcs|iha|ira|idn|ssp))\)(?!\s*,))))?(\s*,\s*((?P<reg2b>([a-z][a-z0-9][0-9]?|zero|pcs|iha|ira|idn|ssp))|((?P<immb>[\w\-]+)\((?P<reg2c>([a-z][a-z0-9][0-9]?|zero|pcs|iha|ira|idn|ssp))\))))?(\s*,\s*((?P<reg3>([a-z][a-z0-9][0-9]?|zero|pcs|iha|ira|idn|ssp))|(?P<immc>[\w\-]+)))?)(\s*(?P<comment>;.+))?(?:\s*(\r|\n))$', re.I) #done
commentRegex = re.compile('^\s*(?P<comment>;.+)?(?:\r|\n)') #done
labelRegex = re.compile('^\s*(?P<label>[\w\-]+):(\s*(?P<comment>;.+))?(?:\s*(\r|\n))$') #done

labelRep = {}
nameRep = {}

regMap = {'zero': 'r0',
		  'a0': 'r1',
		  'a1': 'r2',
		  'a2': 'r3',
		  'a3': 'r4',
		  'rv': 'r5',
		  't0': 'r8',
		  't1': 'r9',
		  't2': 'r10',
		  't3': 'r11',
		  't4': 'r12',
		  't5': 'r13',
		  't6': 'r14',
		  't7': 'r15',
		  's0': 'r16',
		  's1': 'r17',
		  's2': 'r18',
		  's3': 'r19',
		  's4': 'r20',
		  's5': 'r21',
		  's6': 'r22',
		  's7': 'r23',

		  'ssp': 'r24',

		  'gp': 'r28',
		  'fp': 'r29',
		  'sp': 'r30',
		  'ra': 'r31',

		  'ira': 'x0',
		  'iha': 'x1',
		  'idn': 'x2',
		  'pcs': 'x3'}

opMap = {'alur' : 0b00000,
         'lw'   : 0b01010,
         'sw'   : 0b01110,
         'beq'  : 0b10000,
         'blt'  : 0b10001,
         'ble'  : 0b10010,
         'bne'  : 0b10011,
         'jal'  : 0b10111,
         'addi' : 0b11000,
         'andi' : 0b11100,
         'ori'  : 0b11101,
         'xori' : 0b11110,
  
         'sub'  : 0b01000,
         'nand' : 0b01100,
         'nor'  : 0b01101,
         'nxor' : 0b01110,
         'eq'   : 0b10000,
         'lt'   : 0b10001,
         'le'   : 0b10010,
         'ne'   : 0b10011,
         'add'  : 0b11000,
         'and'  : 0b11100,
         'or'   : 0b11101,
         'xor'  : 0b11110,

         'sysp' : 0b00111,
         'sys'  : 0b00000,
         'reti' : 0b10000,
         'rsr'  : 0b10001,
         'wsr'  : 0b10010}


instCounter = 0

for line in foIn:
	line = line.lower()
	m = labelRegex.match(line)

	if m != None:
		labelRep[m.group('label')] = "{0:#010x}".format(instCounter*4)
		continue

	m = pragmaRegex.match(line)

	if m != None:
		pragmaInst = m.group('pragma')

		if pragmaInst == "orig":
			destCounter = int(m.group('name'), 0) / 4

			if destCounter != instCounter:
				instCounter = destCounter

		elif pragmaInst == "word":
			instCounter += 1


	m = instRegex.match(line)

	if m != None:
		instCounter += 1
	

foIn.seek(0)
instCounter = 0

for line in foIn:
	m = commentRegex.match(line)

	if m != None:
		#print m.group('comment')
		continue

	line = line.lower()
	m = labelRegex.match(line)

	if m != None:
		#print m.group('label')
		continue

	m = pragmaRegex.match(line)

	if m != None:
		#print m.group('pragma'),m.group('name'),m.group('value')

		pragmaInst = m.group('pragma')

		if pragmaInst == "orig":
			destCounter = int(m.group('name'), 0) / 4

			if destCounter != instCounter:
				foOut.write("[" + "{0:08x}".format(instCounter) + ".." + "{0:08x}".format(destCounter-1) + "] : DEAD;\n")
				instCounter = destCounter
		elif pragmaInst == "word":
			foOut.write("-- @ " + "{0:#010x}".format(instCounter*4) + " : " + m.group() + "\n")
			foOut.write("{0:08x}".format(instCounter) + " : " + "{0:08x}".format(int(m.group('name'), 0)) + ";\n")
			instCounter += 1
		elif pragmaInst == "name":
			nameRep[m.group('name')] = m.group('value')
		else:
			raise Exception("Pragma " + m.group('pragma') + " is invalid.")


	m = instRegex.match(line)

	if m != None:
		#print m.group('inst'),m.group('reg1'),m.group('reg2a'),m.group('reg2b'),m.group('reg2c'),m.group('reg3'),m.group('imma'),m.group('immb'),m.group('immc')

		inst = None
		reg1 = None
		reg2 = None
		reg3 = None
		imm = None

		inst = m.group('inst')
		reg1 = m.group('reg1')
		reg3 = m.group('reg3')

		if m.group('reg2a') != None:
			reg2 = m.group('reg2a')
		elif m.group('reg2b') != None:
			reg2 = m.group('reg2b')
		elif m.group('reg2c') != None:
			reg2 = m.group('reg2c')


		if m.group('imma') != None:
			imm = m.group('imma')
		elif m.group('immb') != None:
			imm = m.group('immb')
		elif m.group('immc') != None:
			imm = m.group('immc')


		if reg1 in regMap:
			reg1 = regMap[reg1]

		if reg2 in regMap:
			reg2 = regMap[reg2]

		if reg3 in regMap:
			reg3 = regMap[reg3]


		if imm in nameRep:
			imm = nameRep[imm]

		if imm in labelRep:
			if inst == "beq" or inst == "blt" or inst == "ble" or inst == "bne" or inst == "bgt" or inst == "bge":
				imm = "{0:#010x}".format(int(labelRep[imm], 0)/4-instCounter-1)

			elif inst == "jal" or inst == "call" or inst == "jmp":
				imm = "{0:#010x}".format(int(labelRep[imm], 0)/4)

			else:
				imm = "{0:#010x}".format(int(labelRep[imm], 0))


		if reg1 != None:
			reg1 = int(reg1[1:])

		if reg2 != None:
			reg2 = int(reg2[1:])

		if reg3 != None:
			reg3 = int(reg3[1:])

		if imm != None:
			imm = int(imm, 0)


		if inst == "not":
			inst = "xori"
			imm = -1

		elif inst == "call":
			inst = "jal"
			reg1 = int(regMap['ra'][1:])

		elif inst == "ret":
			inst = "jal"
			reg1 = 6
			reg2 = int(regMap['ra'][1:])
			imm = 0

		elif inst == "jmp":
			inst = "jal"
			reg1 = 6

		elif inst == "bgt":
			inst = "blt"
			reg1 ^= reg2
			reg2 ^= reg1
			reg1 ^= reg2

		elif inst == "bge":
			inst = "ble"
			reg1 ^= reg2
			reg2 ^= reg1
			reg1 ^= reg2		

		elif inst == "gt":
			inst = "lt"
			reg2 ^= reg3
			reg3 ^= reg2
			reg2 ^= reg3

		elif inst == "ge":
			inst = "le"
			reg2 ^= reg3
			reg3 ^= reg2
			reg2 ^= reg3

		elif inst == "subi":
			inst = "addi"
			imm = -imm


		if inst == "beq" or inst == "blt" or inst == "ble" or inst == "bne":
			reg1 ^= reg2
			reg2 ^= reg1
			reg1 ^= reg2
		

		if inst == "nop":
			compiledInst = "{0:08x}".format(0)

		elif inst == "reti" or inst == "sys":
			compiledInst = "{0:08x}".format(opMap['sysp'] << 27 | opMap[inst])

		elif inst == "rsr" or inst == "wsr":
			compiledInst = "{0:08x}".format(opMap['sysp'] << 27 | reg1 << 22 | reg2 << 17 | opMap[inst])

		elif imm != None:
			compiledInst = "{0:08x}".format(opMap[inst] << 27 | reg2 << 22 | reg1 << 17 | (imm & 0x1FFFF))

		else:
			compiledInst = "{0:08x}".format(opMap['alur'] << 27 | reg2 << 22 | reg3 << 17 | reg1 << 12 | opMap[inst])


		foOut.write("-- @ " + "{0:#010x}".format(instCounter*4) + " : " + m.group('all').upper() + "\n")
		foOut.write("{0:08x}".format(instCounter) + " : " + compiledInst + ";\n")

		instCounter += 1


foOut.write("[" + "{0:08x}".format(instCounter) + "..000007ff] : DEAD;\n")
foOut.write("END;")

foIn.close()
foOut.close()
