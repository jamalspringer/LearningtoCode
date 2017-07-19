
DailyRate = int(raw_input("Insert daily rate : "))

def WageCalc(DailyRate):
    Daily = DailyRate
    Weekly = DailyRate * 5
    Monthly = Weekly * 4
    Annualy = Monthly * 12
    Tax = Monthly * 0.20
    AnuualAfterTax = Annualy - Tax
    print "Your Daily Rate is %s" % Daily
    print "Your Weekly Rate is %s" % Weekly
    print "Your Monthly Rate is %s" % Monthly
    print "Your Annual Rate is %s" % Annualy
    print "You will receive approx %s after tax annually" % AnuualAfterTax
    input("Press any ket to exit")
WageCalc(DailyRate)