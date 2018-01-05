
class Human
  def initialize(name, age, gender, nationality, race)
    @name = name
    @age = age
    @gender = gender
    @nationality = nationality
    @race = race
  end


  public

  def greet(person="")
    puts "Hello #{person}, How are you ?"
  end

  def introduce(person="")
    puts "Hello #{person}, my name is #{@name},i'm #{@age} years old & i'm #{@nationality}"
  end

  def conversate(words="")
    puts words
  end

  def study(subject="Software development", hours=1)
    if hours == 1
      puts "Currently studying #{subject} for an hour"
    else
      puts "Currently studying #{subject} for #{hours} hours"
    end
  end

end

jspringer = Human.new("Jamal Springer", 24, "Male", "British", "Black")

jspringer.greet("Steve")
jspringer.introduce("Bobby")
jspringer.conversate("Blah Blah Blah, Yada Yada Yada & yeah my weekend was amazing!")
jspringer.study("Coding Ruby", 3)
