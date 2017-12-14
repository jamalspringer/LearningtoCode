
def yeelder
  puts "Only prints this and whatever you pass me in a block"
  yield
end

yeelder {puts "Blah Blah"}




def tester()
  yield
end


Hooloo = Proc.new do
puts "hmmmm"
puts "This is a method which does nothing, apart from take the yield you give it"
end

tester() {Hooloo}




















