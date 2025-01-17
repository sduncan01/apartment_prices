declare -a cities=("test" "bos" "den" "sfo" "chi" "wma" "nyc" "dc" "sea" "nm1" "nm2" "vt1" "vt2" "stl" "sd" "por" "pme" "pit" "slo" "phi2")
for i in "${cities[@]}"
do
	echo "$i"
	mkdir -p "$i"
	cd "$i"
	python3 ../query_padmapper.py dl1.txt proc1.txt "$i"
	python3 ../draw_heatmap.py proc1.txt "$i"
	cp ../maps/"$i".png "$i"Map.png
	convert $(find . -type f -name 'proc1.txt.phantom.*.png') -channel A -evaluate Multiply 0.5 +channel "$i"Transparent.png
	composite "$i"Transparent.png "$i"Map.png "$i"Out.png
	cd ..
done

