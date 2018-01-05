#Comic Book Hero/Villain class

class Comicbookcharacter
  def initialize(name = "", creator = "", alter_ego = "", publisher = "", attributes = {}, archenemy = "")
    @name = name
    @creator = creator
    @alter_ego = alter_ego
    @publisher = publisher
    @attributes = attributes
    @archenemy = archenemy
  end

public

  def set_name(name)
    @name = name
  end

  def get_name()
    return @name
  end

  def set_alter_ego(ae)
    @alter_ego = ae
  end

  def get_alter_ego()
    return @alter_ego
  end

  def set_publisher(publisher)
    @publisher = publisher
  end

  def get_publisher()
    return @publisher
  end

  def print_all()
    puts "Name: #{@name}"
    puts "Creator: #{@creator}"
    puts "Alter ego: #{@alter_ego}"
    puts "Publisher: #{@publisher}"
    puts "Attributes: #{@attributes}"
    puts "Archenemy: #{@archenemy}"
  end

end

class Hero < Comicbookcharacter
end

class Villain < Comicbookcharacter
end
