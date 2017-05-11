test_list = {"1": {"up": 2, "down": 3},
             "7": {"up": 8, "down": 9}}

test_list["1"]["up"] += 10
print test_list

if "2" in test_list:
    print "Found inside"
else:
    print "Not Found"