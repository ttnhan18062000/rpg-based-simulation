import json,sys,collections
d=json.load(open(sys.argv[1])); dd=d["deaths"]
none=[x for x in dd if x[3] is None]
near0=[x for x in none if abs(x[4][0])<=10 and abs(x[4][1])<=10]
print(sys.argv[2],"| deaths:",len(dd),"| credited to no region:",len(none),"(%.0f%%)"%(100*len(none)/max(1,len(dd))),"| of those within 10 of origin:",len(near0))
print("   causes of uncredited:",dict(collections.Counter(("passive:"+x[7].split(".")[-1]) if x[7]!="None" else x[6] for x in none)))
print("   cause of ALL deaths:",dict(collections.Counter(("passive:"+x[7].split(".")[-1]) if x[7]!="None" else x[6] for x in dd)))
print("   uncredited positions:",sorted({(round(x[4][0]),round(x[4][1])) for x in none})[:14])
