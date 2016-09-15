import cdb
import operator

if "__main__" == __name__:
    db = cdb
    list1 = db.read_db('patients.xdb')
    sorted_x = sorted(list1.iteritems(), key=operator.itemgetter(0))
    for p in sorted_x:
        print p[0] + ", " + p[1]
