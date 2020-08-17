list1 = [2, 45, 65, 82, 121, 332]
list2 = [53, 122, 789, 3231, 3344, 5454]
list3 = [12, 42, 54, 55, 78, 532, 5656]

a = b = c = 0
count = 0
k = int(input('enter the number'))

while count <= k:
    if list1[a] <= list2[b]:
        if list1[a] <= list3[c]:
            if count == k:
                print(list1[a])
                break
            a = a + 1
        else:
            if count == k:
                print(list3[c])
                break
            c = c + 1
    else:
        if list3[c] <= list2[b]:
            if count == k:
                print(list3[c])
                break
            c = c + 1
        else:
            if count == k:
                print(list3[b])
                break
            b = b + 1

    count = count + 1

