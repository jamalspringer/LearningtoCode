#Simple word calculator...
puts ""
puts "Ruby version: #{RUBY_VERSION}"
puts ""

one = 1
two = 2
three = 3
four = 4
five = 6
six = 6
seven = 7
eight = 8
nine = 9
ten = 10

puts one * four
puts nine * ten

def getversion(current=RUBY_VERSION, upgrade)
  puts "The current ruby version is #{current}"
  puts "..........."
  puts "..........."
  puts "Upgradring to #{upgrade}"
end

def rand_num_gen()
  return rand(1..10)
end


  getversion("1.#{rand_num_gen}.#{rand_num_gen}", "5.0.0")

