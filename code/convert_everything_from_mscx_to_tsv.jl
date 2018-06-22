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
    # translate xml durations
    durationdict = Dict(
        "measure" => 1.0,
        "whole"   => 1/1,
        "half"    => 1/2,
        "quarter" => 1/4,
        "eighth"  => 1/8,
        "16th"    => 1/16,
        "32nd"    => 1/32,
        "64th"    => 1/64,
        "128th"   => 1/128
    )

    # find first staff
    xroot           = root(parse_file(filename))
    first_staff     = find_element(find_element(xroot, "Score"), "Staff")

    # initialize column vectors
    chords          = String[]
    altchords       = String[]
    measure_numbers = Int[]
    beat_numbers    = Float64[]
    total_beats     = Float64[]
    time_sigs       = String[]

    beats_per_measure = 0.0
    sum_of_beats      = 0.0 # sum beats of all previous bars
    time_sig          = ""

     # maps a tuplet id to its scaling factor
    tuplets = Dict{Int, Float64}()

    measure_nodes = get_elements_by_tagname(first_staff, "Measure")

    # calculate first measure number
    m1, m2 = measure_nodes[1:2]
    first_measure_number =
        if attribute(m1, "number") == "1"
            attribute(m2, "number") == "1" ? 0 : 1
        else
            attribute(m1, "number") == "1"
            # error("Wrong numbering of the first bar.")
        end

    for measure_node in get_elements_by_tagname(first_staff, "Measure")
        measure_number =
            if attribute(measure_node, "number") == "1" && has_attribute(measure_node, "len")
                first_measure_number
            else
                parse(Int, attribute(measure_node, "number"))
            end

        is_upbeat_measure =
            attribute(measure_node, "number") == "1" && has_attribute(measure_node, "len")

        beat = chord_beat = if is_upbeat_measure
            eval(parse(attribute(measure_node, "len"))) * 4
        else
            1.0
        end

        for node in child_elements(measure_node)
            if name(node) == "TimeSig"
                n = content(find_element(node, "sigN"))
                d = content(find_element(node, "sigD"))
                time_sig = "$n/$d"
                beats_per_measure = 4 * parse(Float64, n) / parse(Float64, d)
                continue
            elseif name(node) == "Harmony"
                symbols = split(content(find_element(node, "name")), '-')
                push!(chords, symbols[1])
                push!(altchords, length(symbols) == 2 ? symbols[2] : "")
                push!(measure_numbers, measure_number)
                push!(beat_numbers, beat)
                push!(total_beats, sum_of_beats + beat)
                push!(time_sigs, time_sig)
                continue
            elseif name(node) == "Chord" || name(node) == "Rest"
                isa_grace_note = true in
                    [ismatch(r"grace", name(n)) for n in child_elements(node)]
                if isa_grace_note continue end

                basic_value = durationdict[
                    content(find_element(node, "durationType"))]

                dot_value = let n = find_element(node, "dots")
                    n != nothing ? parse(Float64, content(n)) : 0.0
                end

                scaling_factor = let n = find_element(node, "Tuplet")
                    n != nothing ? tuplets[parse(Int, content(n))] : 1.0
                end

                chord_beat += sum(basic_value/(2^d) for d in 0:dot_value) *
                    4 * scaling_factor

                beat = chord_beat
            elseif name(node) == "tick"
                # the first note is on beat 1
                total_beat = parse(Float64, content(node))/480 + 1.0
                beat = total_beat - sum_of_beats
            elseif name(node) == "Tuplet"
                scaling_factor =
                    parse(Float64, content(find_element(node, "normalNotes"))) /
                    parse(Float64, content(find_element(node, "actualNotes")))
                tuplets[parse(Int, attribute(node, "id"))] = scaling_factor
            end
        end
        sum_of_beats += if is_upbeat_measure
            eval(parse(attribute(measure_node, "len"))) * 4
        else
            beats_per_measure
        end
    end

    op, no, mov = let
        m = match(r"op(\d+)_no(\d+)_mov(\d+)\.mscx", splitdir(filename)[2])
        m[1], m[2], m[3]
    end

    DataFrame(
        chord=chords,
        altchord=altchords,
        measure=measure_numbers,
        beat=beat_numbers,
        totbeat=total_beats,
        timesig=time_sigs,
        op=op, no=no, mov=mov)
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
        out = splitext(file)[1] * ".tsv"
        try
            df = read_chords(joinpath(mscx_dir, dir, file))
            out = splitext(file)[1] * ".tsv"
            writetable(joinpath(tsv_dir, dir, out), df)
        catch e
            println(file)
            sleep(3)
            throw(e)
        end
    end
end
