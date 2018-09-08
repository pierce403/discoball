pragma solidity ^0.4.23;

contract DiscoBall
{
    event DiscoMsg(address publisher, string hash, string description,uint count);
    DiscoData public discoData;

    address owner;

    constructor() public
    {
        owner=msg.sender;
        discoData=DiscoData(0x85D6cC7bb4A2d702dffbD390DC93d5dA60e7B40d);
    }

    function insert(string hash, string description) public
    {
        uint count = discoData.insert(hash,description);
        emit DiscoMsg(msg.sender,hash,description,count);
    }

    function bump(uint target) public
    {
        discoData.bump(target);
    }

    function stomp(uint target) public
    {
        discoData.stomp(target);
    }
}

contract DiscoData{

  address owner;
  address[] public publishers;
  string[] public hashes;
  string[] public descriptions;
  uint[] public scores;

  constructor() public {
      owner=msg.sender;
  }

  function insert(string hash, string description) public returns(uint)
  {
    assert(bytes(hash).length==46);
    assert(bytes(description).length<=64);

    publishers.push(tx.origin);
    hashes.push(hash);
    descriptions.push(description);
    scores.push(0);

    return hashes.length;
  }

  function count() external view returns (uint256) {
      return hashes.length;
  }

  function bump(uint target) external {

      require(target<scores.length);
      scores[target]=scores[target]+1;
  }

  function stomp(uint target) external
  {
      // make sure people can wipe their own data
      require((tx.origin == publishers[target]) || (msg.sender == owner));

      publishers[target]=0;
      hashes[target]="";
      descriptions[target]="";
      scores[target]=0;
  }
}
