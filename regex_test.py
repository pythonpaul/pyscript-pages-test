addr1 = "4 CHELMSLEY CT TOLEDO OH43615"
addr2 = "2324 WASHINGTON RD APT A10 WASHINGTON IL61571"

addr_list = addr2.split(" ")
print(addr_list)

city = addr_list[-2]
state = addr_list[-1][0:2]
zip = addr_list[-1][2:]

print("city: "+city+'\n',"state: " + state  + '\n',"zip: " + zip + '\n')  

