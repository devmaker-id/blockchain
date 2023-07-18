# blockchain
untuk installasi menggunakan python3 <br>
$ pip3 install flask <br>
$ pip3 install requests <br>
<hr>
menjalankan server.py [port] <br>
contoh : $ server.py 5010 <br>
akan berjalan di. <br>
http://localhost:5010 <br>
<hr>
route bisa dilihat di coding <br>
@app.route

<hr>
sebagai contoh saya menggunakan port 5010 [http://localhost:5010] <br>
http://localhost:5010/blockchain [GET] -> melihat semua block <br>
http://localhost:5010/mine [GET] -> mining block <br>
<code>
  response = {
        'message': "Block baru telah ditambahkan (mined)",
        'index': block['index'],
        'hash_of_previous_block' : block['hash_of_previous_block'],
        'nonce': block['nonce'],
        'transaction': block['transaction']
    }
</code>
http://localhost:5010/transactions/new [POST] -> membuat transaksi baru <br>
<code>
  {
    'sender':'DevNet00000000001,
    'recipient':'DevNet00099999991',
    'amount':10
  }
</code>
http://localhost:5010/nodes/add_nodes [POST] -> MENAMBAH NODE BARU <br>
http://localhost:5010/nodes/sync [GET] -> singkronisasi semua blok <br>
