"""
Receives the fourier modes in text format and creates
an xml file with a variation of +-20% in the possible
values
"""

index=151
subindex=0
with open("input.txt") as f:
	for line in f:
		xy=line.partition('(')[-1].partition(')')[0]
		vals=[]
		vals=xy.split(',')
		valx=int(vals[0])
		valy=int(vals[1])
		valrbc=float(line.partition('=')[-1].partition('ZBS')[0])
		valzbs=float(line.rpartition('=')[-1])
		
		min_value=valrbc-(abs(valrbc)*0.2)
		max_value=valrbc+(abs(valrbc)*0.2)
		gap=(abs(max_value)-abs(min_value))/1000.0
		if (max_value<=min_value):
			print "ERROR1"
			print line

		print ("	<param>")
		print ("		<index>" + str(index) + "</index>")
		index+=1
		print ("		<name>rbc"+str(subindex)+"</name>")
		print ("		<value x=\""+ str(valx) + "\" y=\"" + str(valy) + "\">" + str(valrbc) + "</value>")
		print ("		<type>double</type>")
		print ("		<display>True</display>")
		print ("		<fixed>False</fixed>")
		print ("		<gap>"+str(gap)+"</gap>")

		print ("		<min_value>"+str(min_value)+"</min_value>")
		print ("		<max_value>"+str(max_value)+"</max_value>")
		print ("	</param>")
 
		min_value=valzbs-(abs(valzbs)*0.2)
		max_value=valzbs+(abs(valzbs)*0.2)
		if (max_value<=min_value):
			print "ERROR2"
			print line
		gap=(abs(max_value)-abs(min_value))/1000.0

                print ("	<param>")
                print ("		<index>" + str(index) + "</index>")
                index+=1
                print ("		<name>zbs"+str(subindex)+"</name>")
		print ("		<value x=\""+ str(valx) + "\" y=\"" + str(valy) + "\">" + str(valzbs) + "</value>")
                print ("		<type>double</type>")
                print ("		<display>True</display>")
                print ("		<fixed>False</fixed>")
                print ("		<gap>"+str(gap)+"</gap>")
                print ("		<min_value>"+str(min_value)+"</min_value>")
                print ("		<max_value>"+str(max_value)+"</max_value>")
                print ("	</param>")
		subindex+=1
