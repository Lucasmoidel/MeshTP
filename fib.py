numbers=[0, 1]
for i in range(2, 200):
    numbers.append(numbers[i-1]+numbers[i-2])
print(numbers)
f = open("testfile.txt", "w")
for x in numbers:
    f.write(str(x) + "\n")
f.close()