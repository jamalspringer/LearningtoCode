
def yeelder
  puts "Only prints this and whatever you pass me in a block"
  yield
end

yeelder {puts "Blah Blah"}



