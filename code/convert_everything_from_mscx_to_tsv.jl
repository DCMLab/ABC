using LightXML, DataFrames

"simple version of read_chord, does not calculate the beat information"
function read_chords_with_measure_numbers(filename)
  xroot = root(parse_file(filename))
  first_staff = find_element(find_element(xroot, "Score"), "Staff")
  chords = DataArray{String}([])
  altchords = DataArray{String}([])
  measure_numbers = DataArray{Int}([])
  for measure_node in get_elements_by_tagname(first_staff, "Measure")
    for harmony_node in get_elements_by_tagname(measure_node, "Harmony")
      symbols = split(content(find_element(harmony_node, "name")), '-')
      push!(chords, symbols[1])
      push!(altchords, length(symbols) == 2 ? symbols[2] : NA)
      push!(measure_numbers, parse(Int, attribute(measure_node, "number")))
    end
  end
  DataFrame(chords=chords, altchords=altchords, measure=measure_numbers)
end

"calculates a DataFrame with chord symbols, including measure and beat information"
function read_chords(filename)
  durationdict = Dict("measure"=>1.0,"whole"=>1/1,"half"=>1/2,"quarter"=>1/4,"eighth"=>1/8,"16th"=>1/16,"32nd"=>1/32,"64th"=>1/64,"128th"=>1/128)
  xroot = root(parse_file(filename))
  first_staff = find_element(find_element(xroot, "Score"), "Staff")

  chords = DataArray{String}([])
  altchords = DataArray{String}([])
  measure_numbers = DataArray{Int}([])
  beat_numbers = DataArray{Float64}([])

  beats_per_measure = 0.0 # initialization is needed
  tuplets = Dict{Int, Float64}() # maps a tuplet id to its scaling factor
  for measure_node in get_elements_by_tagname(first_staff, "Measure")
    beat = 1.0 # the current chord symbol offset
    chord_beat = 1.0 # the current note offset
    for node in collect(child_elements(measure_node))
      if name(node) == "TimeSig"
        beats_per_measure = 4 * parse(Float64, content(find_element(node, "sigN"))) /
                                parse(Float64, content(find_element(node, "sigD")))
        continue
      elseif name(node) == "Harmony"
        symbols = split(content(find_element(node, "name")), '-')
        push!(chords, symbols[1])
        push!(altchords, length(symbols) == 2 ? symbols[2] : NA)
        push!(measure_numbers, parse(Int, attribute(measure_node, "number")))
        push!(beat_numbers, beat)
        continue
      elseif name(node) == "Chord" || name(node) == "Rest"
        isgrace = false # do not count the beat if the note is a grace note
        for n in collect(child_elements(node))
          if ismatch(r"grace", name(n))
            isgrace = true
            break
          end
        end
        if isgrace continue end

        basic_value = durationdict[content(find_element(node, "durationType"))]
        if find_element(node, "dots") != nothing
          dot_value = parse(Float64, content(find_element(node, "dots")))
        else
          dot_value = 0.0
        end

        if find_element(node, "Tuplet") != nothing
          scaling_factor = tuplets[parse(Int, content(find_element(node, "Tuplet")))]
        else
          scaling_factor = 1.0
        end

        chord_beat += sum([basic_value/(2^d) for d in 0:dot_value]) * 4 * scaling_factor
        beat = chord_beat
        continue
      elseif name(node) == "tick"
        total_beat = parse(Float64, content(node))/480 + 1.0 # the first note is on beat 1
        measure_number = parse(Float64, attribute(measure_node, "number"))
        beat = total_beat - beats_per_measure * (measure_number - 1)
        continue
      elseif name(node) == "Tuplet"
        scaling_factor = parse(Float64, content(find_element(node, "normalNotes"))) /
                         parse(Float64, content(find_element(node, "actualNotes")))
        tuplets[parse(Int, attribute(node, "id"))] = scaling_factor
        continue
      end
    end
  end
  DataFrame(chords=chords, altchords=altchords, measure=measure_numbers, beat=beat_numbers)
end


mscx_dir = joinpath(@__DIR__, "..", "data", "mscx")

tsv_dir = let dir = joinpath(@__DIR__, "..", "data", "tsv")
    if !isdir(dir)
        mkdir(dir)
    end
    dir
end

for dir in filter(d->isdir(joinpath(mscx_dir, d)), readdir(mscx_dir))
    if !isdir(joinpath(tsv_dir, dir))
        mkdir(joinpath(tsv_dir, dir))
    end
    for file in filter(f->ismatch(r".mscx", f), readdir(joinpath(mscx_dir, dir)))
        df = read_chords(joinpath(mscx_dir, dir, file))
        out = splitext(file)[1] * ".tsv"
        writetable(joinpath(tsv_dir, dir, out), df)
    end
end
