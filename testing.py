
r = input("Enter rows (9 digits blocks, comma-separated)\n")

while True:
    try:
        a = r.replace(',', '')
        a.isdigit()
        if len(a) != 81:
            raise Exception
        del a
        break
    except:
        r = input("Wrong entry.\nEnter rows (9 digits blocks, comma-separated)\n")


list = r.split(',')

for i in range(0, len(list)):
    if sorted(list[i]) != ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
        print('No:', list[i])
        exit(0)
a = ''
b = ''
c = ''
for i in range(0,3):
    a += (list[i][0:3])
    b += (list[i][3:6])
    c += (list[i][6:9])
if sorted(a) != sorted(b) != sorted(c) != ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
    print('No:', list[i])
    exit(0)
a = ''
b = ''
c = ''
for i in range(3,6):
    a += (list[i][0:3])
    b += (list[i][3:6])
    c += (list[i][6:9])
if sorted(a) != sorted(b) != sorted(c) != ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
    print('No:', list[i])
    exit(0)
a = ''
b = ''
c = ''
for i in range(6,9):
    a += (list[i][0:3])
    b += (list[i][3:6])
    c += (list[i][6:9])
if sorted(a) != sorted(b) != sorted(c) != ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
    print('No:', list[i])
    exit(0)

print("Yes")

