import json
import sys
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
import os.path
from subprocess import PIPE
import subprocess
import shlex
import time

# usage:
# python3 query_padmapper.py test/dl1.txt test/proc1.txt

# default
MIN_LAT = 42.2 
MAX_LAT = 42.21
MIN_LON = -71.1
MAX_LON = -71.09

class AreaTooLarge(Exception):
  pass

def direct_fetch(cmd_prefix, minLat, minLng, maxLat, maxLng, it):
  args = shlex.split(cmd_prefix)
  args.append("--data-raw")
  # You would think we could just use offset, but that's not actually respected
  # by the backend.
  args.append(json.dumps(
    {'limit': 100,
     'box': {'maxLat': maxLat,
             'minLat': minLat,
             'maxLng': maxLng,
             'minLng': minLng},
     'propertyTypes': {'include': [4, 15, 5, 14, 9, 1, 3, 6, 13, 21],
                       'exclude': [16, 17]},
     'external': True}))
  args.append('--compressed')
  args.append('-sS')
  time.sleep(1)

  result = json.loads(subprocess.check_output(args))

  if (type(result) != type({}) or
      "pins" not in result or
      type(result["pins"]) != type([])):
    import pprint
    pprint.pprint(result)
    with open("tmp.json", "w") as outf:
      json.dump(result, outf)
    raise Exception("bad response")

  result = result["pins"]
  
  if len(result) > 99:
    if it > 30: # depth of 50 was taking excessively long for Philadelphia
      # we've already tried to zoom in too far here, and now we're stuck.
      # import pprint
      # pprint.pprint(result)
      print("using first 100 results from this location")
    else:
      raise AreaTooLarge()

  return result

def intermediate(minVal, maxVal):
  return (maxVal-minVal)/2 + minVal

def fetch(cmd_prefix, minLat, minLng, maxLat, maxLng, it=0):
  print(('%s %.10f %.10f %.10f %.10f' % ('  '* it, minLat, minLng, maxLat, maxLng)))

  def fetchHelper(minLat, minLng, maxLat, maxLng):
    return fetch(cmd_prefix, minLat, minLng, maxLat, maxLng, it+1)

  try:
    return direct_fetch(cmd_prefix, minLat, minLng, maxLat, maxLng, it)
  except AreaTooLarge:
    if it % 2:
      return (fetchHelper(minLat, minLng, intermediate(minLat, maxLat), maxLng) +
              fetchHelper(intermediate(minLat, maxLat), minLng, maxLat, maxLng))
    else:
      return (fetchHelper(minLat, minLng, maxLat, intermediate(minLng, maxLng)) +
              fetchHelper(minLat, intermediate(minLng, maxLng), maxLat, maxLng))

def download(fname):
 # print("Visit:")
 # print('https://www.padmapper.com/apartments/belmont-ma/belmont-hill?box=-71.1993028524,42.396054506,-71.1761285665,42.4262507215&property-categories=apartment')
 # print("Inspect the networking, find a pins request, copy request as curl and paste here.")
 # inp = input("> ")
  print("reading curl example")
  script_dir = os.path.dirname(__file__)
  rel_path = "test_old/curl-example-bos.txt"
  curlf_path = os.path.join(script_dir, rel_path)
  curlf = open(curlf_path, "r")
  inp = curlf.read()
  while inp.endswith("\\"):
    inp = inp[:-2] + " "
    inp += input("> ")

  print ("%r" % inp)

  if "--data-raw" not in inp:
    raise Exception("Something looks wrong.  Was that the curl version of a pins request?")

  cmd_prefix = inp.split("--data-raw")[0]
  result = fetch(cmd_prefix, MIN_LAT, MIN_LON, MAX_LAT, MAX_LON)
  if not result:
    raise Exception("no response")
  with open(fname, 'w') as outf:
    outf.write(json.dumps(result))

def process(fname_in, fname_out):
  with open(fname_in) as inf:
    data = json.loads(inf.read())
  processed = []
  for listing in data:
    lat = listing["lat"]
    lon = listing["lng"]
    bedrooms = listing["min_bedrooms"]
    rent = listing["min_price"]
    apt_id = listing["listing_id"]

    processed.append((rent, bedrooms, apt_id, lon, lat))

  with open(fname_out, "w+") as outf:
    print("writing to %s" % fname_out)
    for rent, bedrooms, apt_id, lon, lat in processed:
      outf.write("%s %s %s %s %s\n" % (rent, bedrooms, apt_id, lon, lat))

def start(fname_download, fname_processed, city):
   
  global MIN_LAT # south
  global MAX_LAT # north
  global MIN_LON # west
  global MAX_LON # east
  
  minLatValues = {"test" : 42.2979,
                  "bos" : 42.23543,
                  "den" : 39.66207,
                  "sfo" : 37.6492,
                  "chi" : 41.7794,
                  "wma" : 42.2475,
                  "nyc" : 40.5656,
                  "dc" : 38.7882,
                  # "phi" : 39.8759,
                  "sea" : 47.5229,
                  "nm1" : 35.5771,
                  "nm2" : 35.0223,
                  "vt1" : 44.3942,
                  "vt2" : 43.5934,
                  "stl" : 38.5623,
                  "sd" : 32.6262,
                  "por" : 45.4207,
                  "pme" : 43.5765,
                  "pit" : 40.3673,
                  "slo" : 35.0945,
                  "phi2" : 39.8812,
  }
  MIN_LAT = minLatValues[city]
   
  maxLatValues = {"test" : 42.3943,
                  "bos" : 42.43925,
                  "den" : 39.8864,
                  "sfo" : 37.8804,
                  "chi" : 41.9841,
                  "wma" : 42.4210,
                  "nyc" : 40.7833,
                  "dc" : 39.0094,
                  # "phi" : 40.0467,
                  "sea" : 47.6898,
                  "nm1" : 35.7553,
                  "nm2" : 35.2298,
                  "vt1" : 44.5588,
                  "vt2" : 43.7343,
                  "stl" : 38.7885,
                  "sd" : 32.8529,
                  "por" : 45.5969,
                  "pme" : 43.7392,
                  "pit" : 40.5084,
                  "slo" : 35.3178,
                  "phi2" : 40.0225,
  }
  MAX_LAT = maxLatValues[city]
  
  minLonValues = {"test" : -71.1667,
                  "bos" : -71.28736,
                  "den" : -105.1604,
                  "sfo" : -122.5240,
                  "chi" : -87.8467,
                  "wma" : -72.7072,
                  "nyc" : -74.0540,
                  "dc" : -77.1656,
                  # "phi" : -75.2955,
                  "sea" : -122.4402,
                  "nm1" : -106.0751,
                  "nm2" : -106.7627, 
                  "vt1" : -73.2884, 
                  "vt2" : -72.3941, 
                  "stl" : -90.4758,
                  "sd" : -117.2918, 
                  "por" : -122.8340,
                  "pme" : -70.4653,
                  "pit" : -80.0467,
                  "slo" : -120.7171, 
                  "phi2" : -75.2642,         
  }
  MIN_LON = minLonValues[city]
    
  maxLonValues = {"test" : -71.0376,
                  "bos" : -70.98803,
                  "den" : -104.81627,
                  "sfo" : -122.1786,
                  "chi" : -87.5662,
                  "wma" : -72.4768,
                  "nyc" : -73.7862,
                  "dc" : -76.9005,
                  # "phi" : -75.0370,
                  "sea" : -122.1649,
                  "nm1" : -105.8505,
                  "nm2" : -106.4623,
                  "vt1" : -73.0230,
                  "vt2" : -72.1929,
                  "stl" : -90.1439,
                  "sd" : -117.0030,
                  "por" : -122.5405,
                  "pme" : -70.2013,
                  "pit" : -79.8490,
                  "slo" : -120.4795,
                  "phi2" : -75.0617,
  }
  MAX_LON = maxLonValues[city]
    
  if not os.path.exists(fname_download):
    download(fname_download)
  if not os.path.exists(fname_download):
    raise Exception("%s still missing" % fname_download)

  if not os.path.exists(fname_processed):
    process(fname_download, fname_processed)
  else:
    print("%s already exists" % fname_processed)

  print("Now you want to use draw_heatmap.py on %s" % fname_processed)

if __name__ == "__main__":
  start(*sys.argv[1:])
